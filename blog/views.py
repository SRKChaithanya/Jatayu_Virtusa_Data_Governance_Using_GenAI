from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from blog.models import Post, Comment, Preference, ToxicComment
import joblib
import os
from django.conf import settings
from users.models import Follow, Profile
import sys
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from .forms import NewCommentForm
from django.contrib.auth.decorators import login_required
from .serializers import UserSerializer, GroupSerializer, PostSerializer
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser 
from rest_framework import status


def is_users(post_user, logged_user):
    return post_user == logged_user


PAGINATION_COUNT = 3


class PostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = PAGINATION_COUNT

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        all_users = []
        data_counter = Post.objects.values('author')\
            .annotate(author_count=Count('author'))\
            .order_by('-author_count')[:6]

        for aux in data_counter:
            all_users.append(User.objects.filter(pk=aux['author']).first())
        # if Preference.objects.get(user = self.request.user):
        #     data['preference'] = True
        # else:
        #     data['preference'] = False
        data['preference'] = Preference.objects.all()
        # print(Preference.objects.get(user= self.request.user))
        data['all_users'] = all_users
        print(all_users, file=sys.stderr)
        return data

    def get_queryset(self):
        user = self.request.user
        qs = Follow.objects.filter(user=user)
        follows = [user]
        for obj in qs:
            follows.append(obj.follow_user)
        return Post.objects.filter(author__in=follows).order_by('-date_posted')


class UserPostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = PAGINATION_COUNT

    def visible_user(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_context_data(self, **kwargs):
        visible_user = self.visible_user()
        logged_user = self.request.user
        print(logged_user.username == '', file=sys.stderr)

        if logged_user.username == '' or logged_user is None:
            can_follow = False
        else:
            can_follow = (Follow.objects.filter(user=logged_user,
                                                follow_user=visible_user).count() == 0)
        data = super().get_context_data(**kwargs)

        data['user_profile'] = visible_user
        data['can_follow'] = can_follow
        return data

    def get_queryset(self):
        user = self.visible_user()
        return Post.objects.filter(author=user).order_by('-date_posted')

    def post(self, request, *args, **kwargs):
        if request.user.id is not None:
            follows_between = Follow.objects.filter(user=request.user,
                                                    follow_user=self.visible_user())

            if 'follow' in request.POST:
                    new_relation = Follow(user=request.user, follow_user=self.visible_user())
                    if follows_between.count() == 0:
                        new_relation.save()
            elif 'unfollow' in request.POST:
                    if follows_between.count() > 0:
                        follows_between.delete()

        return self.get(self, request, *args, **kwargs)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        comments_connected = Comment.objects.filter(post_connected=self.get_object()).order_by('-date_posted')
        data['comments'] = comments_connected
        data['form'] = NewCommentForm(instance=self.request.user)
        return data

    def post(self, request, *args, **kwargs):
        content = request.POST.get('content')
        post = self.get_object()
        
        # Load the toxicity model
        model_path = os.path.join(settings.BASE_DIR, 'models', 'new_model.pkl')
        model = joblib.load(model_path)
        
        # Prepare input and predict toxicity
        from gensim.models import Word2Vec
        import numpy as np
        
        # Load word2vec model
        word2vec_path = os.path.join(settings.BASE_DIR, 'models', 'word2vec_model.model')
        word2vec = Word2Vec.load(word2vec_path)
        word_vectors = word2vec.wv
        



        # Convert text to word vectors
        import google.generativeai as genai
        print('toxic comment',content)
        api_key='AIzaSyDY9wjuzr7N4TXDF6f93JUzDOId6iZhha0'
        genai.configure(api_key=api_key)
        genmini_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        response = genmini_model.generate_content(f"""You are an expert in analysing the sentiment of 
        the given text. Your task is analyse the sentiment of the given text, if it is neutral or 
        positive then give the text as it is , if text is negative then change the sentiment of the 
        text into positive without changing the meaning of the text.Just give me the text and nothing else: {content}.
        if sentiment of text is negative then just add the word "toxic" at the end of the result
        
        
        You are an expert in analysing the sentiment of 
        the given text. You are an AI language model trained to identify and neutralize toxic language while preserving the original intent of a comment. 
        Your task is analyse the sentiment of the given text, if it is neutral or 
        positive then give the text as it is , if text is negative then change the sentiment of the 
        text into neutral without changing the meaning of the text. do not change the point of view of 
        the commentator.Avoid adding or removing information, and ensure that the revised version is free 
        of insults, offensive language, or aggressive phrasing. Just give me the text and nothing else: {content}.
        if sentiment of text is negative then just add the word "toxic" at the end of the result""")
        content=response.text
        print('response',content)
        is_toxic= True if 'toxic' in content else False
        content=content.replace("toxic",' ')
        words = content.split()
        embeddings = [word_vectors[word] for word in words if word in word_vectors]
        #print(embeddings)
        
        # if embeddings:
        #     # Average word vectors
        #     input_data = np.mean(embeddings, axis=0).reshape(1, -1)
        #     print(input_data)

        #     output=model.predict(input_data)[0]
        #     print(output)
        #     is_toxic = True if output > 0.7 else False
        # else:
        #     # If no known words, assume non-toxic
        #     is_toxic = False
        
        if is_toxic:
            # Save to ToxicComment table
            ToxicComment.objects.create(
                content=content,
                author=self.request.user,
                post_connected=post
            )
            # messages.warning(request, 'Toxic comment detected. Please refrain from posting such comments.')
            messages.warning(request, 'Toxic comment detected. We have changed the sentiment of the comment to positive.')
        else:
            # Save to normal Comment table
            Comment.objects.create(
                content=content,
                author=self.request.user,
                post_connected=post
            )
            
        return self.get(self, request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/post_delete.html'
    context_object_name = 'post'
    success_url = '/'

    def test_func(self):
        return is_users(self.get_object().author, self.request.user)


from .forms import PostForm

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_new.html'
    success_url = '/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['tag_line'] = 'Add a new post'
        return data


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_new.html'
    success_url = '/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        return is_users(self.get_object().author, self.request.user)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['tag_line'] = 'Edit a post'
        return data


class FollowsListView(ListView):
    model = Follow
    template_name = 'blog/follow.html'
    context_object_name = 'follows'

    def visible_user(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_queryset(self):
        user = self.visible_user()
        return Follow.objects.filter(user=user).order_by('-date')

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(**kwargs)
        data['follow'] = 'follows'
        return data


class FollowersListView(ListView):
    model = Follow
    template_name = 'blog/follow.html'
    context_object_name = 'follows'

    def visible_user(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_queryset(self):
        user = self.visible_user()
        return Follow.objects.filter(follow_user=user).order_by('-date')

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(**kwargs)
        data['follow'] = 'followers'
        return data


# Like Functionality====================================================================================

@login_required
def postpreference(request, postid, userpreference):
        
        if request.method == "POST":
                eachpost= get_object_or_404(Post, id=postid)

                obj=''

                valueobj=''

                try:
                        obj= Preference.objects.get(user= request.user, post= eachpost)

                        valueobj= obj.value #value of userpreference


                        valueobj= int(valueobj)

                        userpreference= int(userpreference)
                
                        if valueobj != userpreference:
                                obj.delete()


                                upref= Preference()
                                upref.user= request.user

                                upref.post= eachpost

                                upref.value= userpreference


                                if userpreference == 1 and valueobj != 1:
                                        eachpost.likes += 1
                                        eachpost.dislikes -=1
                                elif userpreference == 2 and valueobj != 2:
                                        eachpost.dislikes += 1
                                        eachpost.likes -= 1
                                

                                upref.save()

                                eachpost.save()
                        
                        
                                context= {'eachpost': eachpost,
                                  'postid': postid}

                                return redirect('blog-home')

                        elif valueobj == userpreference:
                                obj.delete()
                        
                                if userpreference == 1:
                                        eachpost.likes -= 1
                                elif userpreference == 2:
                                        eachpost.dislikes -= 1

                                eachpost.save()

                                context= {'eachpost': eachpost,
                                  'postid': postid}

                                return redirect('blog-home')
                                
                        
        
                
                except Preference.DoesNotExist:
                        upref= Preference()

                        upref.user= request.user

                        upref.post= eachpost

                        upref.value= userpreference

                        userpreference= int(userpreference)

                        if userpreference == 1:
                                eachpost.likes += 1
                        elif userpreference == 2:
                                eachpost.dislikes +=1

                        upref.save()

                        eachpost.save()                            


                        context= {'eachpost': eachpost,
                          'postid': postid}

                        return redirect('blog-home')


        else:
                eachpost= get_object_or_404(Post, id=postid)
                context= {'eachpost': eachpost,
                          'postid': postid}

                return redirect('blog-home')



def about(request):
    return render(request,'blog/about.html',)



class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]



@api_view(['GET', 'POST', 'DELETE'])
def post_list(request):
    if request.method == 'GET':
        posts = Post.objects.all()
        
        title = request.query_params.get('title', None)
        if title is not None:
            posts = posts.filter(title__icontains=title)
        
        posts_serializer = PostSerializer(posts, many=True)
        return JsonResponse(posts_serializer.data, safe=False)
        # 'safe=False' for objects serialization
 
    elif request.method == 'POST':
        post_data = JSONParser().parse(request)
        post_serializer = PostSerializer(data=post_data)
        if post_serializer.is_valid():
            post_serializer.save()
            return JsonResponse(post_serializer.data, status=status.HTTP_201_CREATED) 
        return JsonResponse(post_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        count = Post.objects.all().delete()
        return JsonResponse({'message': '{} Posts were deleted successfully!'.format(count[0])}, status=status.HTTP_204_NO_CONTENT)
 
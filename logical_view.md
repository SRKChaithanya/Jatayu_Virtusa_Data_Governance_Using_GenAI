# Logical Functional View - Mermaid Diagram

```mermaid
classDiagram
    %% Entities
    class User {
        +id
        +username
        +email
        +password
    }
    class Profile {
        +profile_pic
        +bio
    }
    class Follow {
        +user_id
        +follow_user_id
        +date
    }
    class Post {
        +id
        +title
        +content
        +date_posted
        +likes
        +dislikes
    }
    class Comment {
        +id
        +content
        +date_posted
    }
    class ToxicComment {
        +id
        +content
        +date_posted
    }
    class Preference {
        +id
        +value
    }

    %% Relationships
    User "1" -- "1" Profile : has
    User "1" -- "0..*" Follow : follows
    User "1" -- "0..*" Post : creates
    Post "1" -- "0..*" Comment : has
    Comment <|-- ToxicComment : extends
    User "1" -- "0..*" Comment : writes
    User "1" -- "0..*" Preference : sets
    Preference "0..*" -- "1" Post : for

    %% Functional Components
    class Registration {
        +registerUser()
    }
    class Login {
        +loginUser()
        +logoutUser()
    }
    class ProfileUpdate {
        +updateProfile()
    }
    class PostCRUD {
        +createPost()
        +readPost()
        +updatePost()
        +deletePost()
    }
    class Commenting {
        +addComment()
        +detectToxicity()
    }
    class Following {
        +followUser()
        +unfollowUser()
    }
    class Liking {
        +likePost()
        +dislikePost()
    }
    class APIEndpoints {
        +userAPI()
        +groupAPI()
        +postAPI()
    }

    %% Functional Components interactions
    Registration ..> User : creates
    Login ..> User : authenticates
    ProfileUpdate ..> Profile : modifies
    PostCRUD ..> Post : manages
    Commenting ..> Comment : creates
    Commenting ..> ToxicComment : flags
    Following ..> Follow : manages
    Liking ..> Preference : manages
    APIEndpoints ..> User : exposes
    APIEndpoints ..> Post : exposes
    APIEndpoints ..> Group : exposes

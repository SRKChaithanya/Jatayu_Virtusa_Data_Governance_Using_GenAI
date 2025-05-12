alert('JavaScript file loaded!');  // Test if file is loading

console.log('comment_toggle.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded event fired');
    
    const toggleButtons = document.querySelectorAll('.toggle-toxic-comment');
    console.log(`Found ${toggleButtons.length} toggle buttons`);
    
    if (toggleButtons.length === 0) {
        console.warn('No toggle buttons found');
        return;
    }

    toggleButtons.forEach((button, index) => {
        console.log(`Setting up listener for button ${index + 1}`);
        button.addEventListener('click', function(e) {
            console.log(`Button ${index + 1} clicked`);
            e.preventDefault();
            e.stopPropagation();
            
            const commentId = this.getAttribute('data-comment-id');
            console.log(`Comment ID: ${commentId}`);
            if (!commentId) {
                console.error('No comment ID found on button');
                return;
            }

            const commentText = document.querySelector(`.toxic-comment[data-comment-id="${commentId}"]`);
            if (!commentText) {
                console.error(`Could not find comment text element for ID: ${commentId}`);
                return;
            }

            const currentFilter = window.getComputedStyle(commentText).filter;
            console.log(`Current filter: ${currentFilter}`);
            commentText.style.filter = currentFilter === 'blur(5px)' ? 'none' : 'blur(5px)';
            
            console.log(`Toggled comment ${commentId}. New filter: ${commentText.style.filter}`);
        });
    });
});

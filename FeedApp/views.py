from django.shortcuts import render, redirect
from .forms import PostForm,ProfileForm, RelationshipForm
from .models import Post, Comment, Like, Profile, Relationship
from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.http import Http404


# Create your views here.

# When a URL request matches the pattern we just defined, 
# Django looks for a function called index() in the views.py file. 

def index(request):
    """The home page for Learning Log."""
    return render(request, 'FeedApp/index.html')



@login_required
def profile(request):
    profile = Profile.objects.filter(user=request.user)
    if not profile.exists():
        Profile.objects.create(user=request.user)
    profile = Profile.objects.get(user=request.user)

    if request.method != 'POST':
        form = ProfileForm(instance=profile)
    else:
        form = ProfileForm(instance=profile, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('FeedApp:profile')
        
    context = {'form': form}
    return render(request, 'FeedApp/profile.html', context)


@login_required
def myfeed(request):
    comment_count_list = []
    like_count_list = []
    posts = Post.objects.filter(username=request.user).order_by('-date_posted')
    for p in posts:
        c_count = Comment.objects.filter(post=p).count()
        l_count = Like.objects.filter(post=p).count()
        comment_count_list.append(c_count)
        like_count_list.append(l_count)
    zipped_list = zip(posts, comment_count_list, like_count_list)

    context = {'posts':posts, 'zipped_list': zipped_list}
    return render(request, 'FeedApp/myfeed.html', context)


@login_required
def friendsfeed(request):
    comment_count_list = []
    like_count_list = []
    friends = Profile.objects.filter(user=request.user).values('friends')
    posts = Post.objects.filter(username__in=friends).order_by('-date_posted')
    for p in posts:
        c_count = Comment.objects.filter(post=p).count()
        l_count = Like.objects.filter(post=p).count()
        comment_count_list.append(c_count)
        like_count_list.append(l_count)
    zipped_list = zip(posts, comment_count_list, like_count_list)

    if request.method == 'POST' and request.POST.get("like"):
        post_to_like = request.POST.get("like")
        print(post_to_like)
        like_already_exists = Like.objects.filter(post_id=post_to_like, username=request.user)
        if not like_already_exists():
            Like.objects.create(post=post_to_like, username=request.user)
            return redirect('FeedApp:friendsfeed')

    context = {'posts':posts, 'zipped_list': zipped_list}
    return render(request, 'FeedApp/myfeed.html', context)


@login_required
def new_post(request):
    if request.method != 'POST':
        form = PostForm()
    else:
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.username = request.user
            new_post.save()
            return redirect('FeedApp:myfeed')
    
    context = {'form': form}
    return render(request, 'FeedApp/new_post.html', context)



@login_required
def comments(request, post_id):
    if request.method == 'POST' and request.POST.get('btn1'):
        comment = request.POST.get("comment")
        Comment.objects.create(post_id=post_id, username=request.user, text=comment, date_added=date.today())

    comments = Comment.objects.filter(post=post_id)
    post = Post.objects.get(id=post_id)

    context = {'post': post, 'comments': comments}
    return render(request, 'FeedApp/comments.html', context)


@login_required
def friends(request):
    # get the admin_profile and user_profule to create the first relationship
    admin_profile = Profile.objects.get(user=1)
    user_profile = Profile.objects.get(user=request.user)

    # to get My Friends
    user_friends = user_profile.friends.all()
    user_friends_profiles = Profile.objects.filter(user__in=user_friends)

    # to get Friend Requests sent
    user_relationships = Relationship.objects.filter(sender=user_profile)
    request_sent_profiles = user_relationships.values('receiver')

    # to get all eligible profiles - exclude the user,  their existing friends, and friend requests already sent
    all_profiles = Profile.objects.exclude(user=request.user).exclude(id_in=user_friends_profiles).exclude(id_in=request_sent_profiles)


    # to get friend requests received by the user
    requests_received_profiles = Relationship.objects.filter(receiver=user_profile, status='sent')

    # if this is the first time to access the friend request page, create the first relationship
    # with the admin of the website

    if not user_relationships.exist():
        Relationship.objects.create(sender=user_profile,receiver=admin_profile, status='sent')

    # check to see WHICH submit button was pressed (sending a friend request or accepting a friend request)

    # this is to process all send requests
    if request.method == 'POST' and request.POST.get("send_request"):
        receivers = request.POST.getlist("send_request")
        for receiver in receivers:
            receiver_profile = Profile.objects.get(id=receiver)
            Relationship.objects.create(sender=user_profile, receiver=receiver_profile, status='sent')
        return redirect('FeedApp:friends')
    
    # this is to process all receive requests
    if request.method == 'POST' and request.POST.get("receive_request"):
        senders = request.POST.getlist("receive_request")
        for sender in senders:
            # update the relationship model for the sender to status 'accepted'
            Relationship.objects.filter(id=sender).update(status='accepted')

            # create a relationship object to access the sender's user id
            # to add to the friends list of the user
            relationship_obj = Relationship.objects.get(id=sender)
            user_profile.friends.add(relationship_obj.sender.user)

            # add the user to the friends list of the sender's profile
            relationship_obj.sender.friends.add(request.user)

    context = {'user_friends_profiles': user_friends_profiles, 'user_relationships': user_relationships,
               'all_profiles': all_profiles, 'requests_received_profiles': requests_received_profiles}
    
    return render(request, 'FeedApp/friends.html', context)

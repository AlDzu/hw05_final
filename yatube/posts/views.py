# posts/views.py
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
# from django.views.decorators.cache import cache_page теперь в шаблоне
from posts.settings import NUMBER_OF_POSTS

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


# @cache_page(20, key_prefix='index_page') теперь в шаблоне
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user_info = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(author=user_info)
    paginator = Paginator(user_posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        following = user_info.following.filter(user=request.user).exists()
    context = {
        'user_info': user_info,  # юзверь
        'user_posts': user_posts,  # его посты
        'page_obj': page_obj,  # что пихнуть на страницу
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    selected_post = get_object_or_404(Post, id=post_id)
    # comments = selected_post.comments.all() теперь достаётся в шаблоне
    comments_form = CommentForm(request.POST or None)
    user_posts = Post.objects.filter(author=selected_post.author)
    post = user_posts.count()
    title = selected_post.text[:30]
    context = {
        'selected_post': selected_post,  # выбранный пост
        'post': post,  # его длина
        'title': title,  # его титул
        # 'comments': comments,
        # # комментарии поста, теперь достаётся в шаблоне
        'comments_form': comments_form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
        )
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    else:
        form = PostForm()
    context = {'form': form}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = get_object_or_404(Post, id=post_id)
        comment.author = request.user
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user).all()
    paginator = Paginator(posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'posts': posts,
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):  # подписка
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author and user not in author.following.all():
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):  # отписка
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=user, author=author).delete()
    return redirect('posts:profile', username)

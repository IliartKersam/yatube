from typing import Type, Union

from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .utils import pag_posts


def index(request: Type[HttpRequest]) -> Type[HttpResponse]:
    """Определяем функцию для главной страницы."""
    post_list: Type[QuerySet] = Post.objects.select_related('author', 'group')
    page_obj = pag_posts(request, post_list)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request: Type[HttpRequest], slug: str) -> Type[HttpResponse]:
    """Определяем функцию для страницы групп."""
    group = get_object_or_404(Group, slug=slug)
    post_list: Type[QuerySet] = group.posts.select_related('author', 'group')
    page_obj = pag_posts(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request: Type[HttpRequest], username: str) -> Type[HttpResponse]:
    """Профиль автора."""
    author = User.objects.get(username=username)
    post_list: Type[QuerySet] = author.posts.select_related('author', 'group')
    page_obj = pag_posts(request, post_list)
    user = request.user
    if not request.user.is_authenticated or request.user == author:
        show_follow = False
    else:
        show_follow = True
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=user, author=author).exists()
    else:
        following = False
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
        'show_follow': show_follow
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: Type[HttpRequest],
                post_id: int) -> Type[HttpResponse]:
    """Детализация поста."""
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.select_related()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request: Type[HttpRequest]) -> (
        Union[Type[HttpResponse],
              Type[HttpResponseRedirect]]):
    """Создаем новый пост."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not request.method == 'POST':
        return render(request, 'posts/create_post.html', {'form': form})
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author.username)


@login_required
def post_edit(request: Type[HttpRequest],
              post_id: int) -> (Union[Type[HttpResponse],
                                      Type[HttpResponseRedirect]]):
    """Редактируем пост."""
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not request.user.username == post.author.username:
        return redirect('posts:post_detail', post.id)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form,
            'is_edit': True
        })
    form.save()
    return redirect('posts:post_detail', post.id)


@login_required
def add_comment(request: Type[HttpRequest],
                post_id: int) -> Type[HttpResponse]:
    """Создаем комментарий к посту."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__following__user=request.user
    )
    page_obj = pag_posts(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    if not Follow.objects.filter(
            user=user, author=author
    ).exists() and not user == author:
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=(username,)))


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    if Follow.objects.filter(user=user, author=author).exists():
        Follow.objects.filter(user=user, author=author).delete()
    return redirect(reverse('posts:profile', args=(username,)))

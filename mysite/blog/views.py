from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.views.generic import ListView
from django.core.mail import send_mail
from django.views.decorators.http import require_POST

from .models import Post
from .forms import EmailPostForm, CommentForm
from taggit.models import Tag


def post_list(request, tag_slug=None):
    posts = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags__in=[tag])

    # Постраничная разбивка с 3 постами на страницу
    paginator = Paginator(posts, 3)
    page_number = request.GET.get('page', 1)

    try:
        posts = paginator.page(page_number)

    except PageNotAnInteger:
        posts = paginator.page(1)

    except EmptyPage:
        # Если page_number находится вне диапазона, то выдать последнюю страницу
        posts = paginator.page(paginator.num_pages)

    return render(request,
                  'blog/post/list.html',
                  {'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        slug=post,
        publish_at__year=year,
        publish_at__month=month,
        publish_at__day=day,
        status=Post.Status.PUBLISHED
    )

    # Список активных комментариев к этому посту
    comments = post.comments.filter(active=True)
    form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)

    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(
        same_tags=Count('tags')
    ).order_by('-same_tags', '-publish_at')[:4]

    return render(
        request,
        "blog/post/detail.html",
        {"post": post, "comments": comments,
         "form": form, 'similar_posts': similar_posts}
    )


def post_share(request, post_id):
    # Извлечь пост по идентификатору id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False

    if request.method == 'POST':
        # Форма была передана на обработку
        form = EmailPostForm(request.POST)

        if form.is_valid():
            # Поля формы успешно прошли валидацию
            cd = form.cleaned_data

            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = (
                f"{cd['name']} рекомендует Вам прочитать запись"
                f"«{post.title}»"
            )

            message = (
                f"Прочитайте «{post.title}» на {post_url}\n\n"
                f"{cd['name']} комментирует: {cd['comments']}"
            )
            send_mail(subject, message,
                      'your_account@gmail.com', [cd['to']])
            sent = True

    else:
        form = EmailPostForm()

    return render(request,
                  'blog/post/share.html',
                  {'post': post, 'form': form, 'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None

    # Комментарий был отправлен
    form = CommentForm(data=request.POST)

    if form.is_valid():
        # Создать объект класса Comment, не сохраняя его в базе данных
        comment = form.save(commit=False)

        # Назначить пост комментарию
        comment.post = post

        # Сохранить комментарий в базе данных
        comment.save()

    return render(request, 'blog/post/comment.html',
                  {'post': post, 'form': form, 'comment': comment})


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = "posts"
    paginate_by = 3
    template_name = 'blog/post/list.html'

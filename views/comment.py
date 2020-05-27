import mistune

from fastapi import APIRouter, Request, Form, Depends
from fastapi_mako import render_template_def
from models import Post, GithubUser

router = APIRouter()

def login_required(f):
    async def wrapper(*args, **kwargs):
        user = request.session.get('user')
        if not user:
            return {'r': 403, 'msg': 'login required'}
        if 'post_id' in request.path_params:
            p_data = await Post.async_first(id=post_id)
            if not p_data:
                return {'r': 1, 'msg': 'no such post.'}
            post = Post(**p_data)
            kwargs['user'] = user
            kwargs['post'] = post
        else:
            kwargs['user'] = user
        return await f(request, *args, **kwargs)
    return wrapper

async def retrieve_user(request: Request):
    user = request.session.get('user')
    if not user:
        return None
    return user

async def retrieve_post(post_id):
    p_data = await Post.async_first(id=post_id)
    if not p_data:
        return None
    return p_data


@router.post('/post/{post_id}/comment')
async def create_comment(request: Request,
                         post_id,
                         content = Form(...)):
    user = await retrieve_user(request)
    if user is None:
        return {'r': 403, 'msg': 'login required'}
    if not content:
        return {'r': 1, 'msg': 'Comment content required.'}
    post_data = await retrieve_post(post_id)
    post = Post(**post_data)
    comment = await post.add_comment(user['gid'], content)
    return {
        'r': 0 if comment else 1,
        'html': await render_template_def(
            'utils.html', 'render_single_comment', request,
            {'comment': comment, 'github_user': user, 'liked_comment_ids': []}
        )
    }

@router.get('/post/{post_id}/comments')
async def comments(request: Request, post_id,
                   page: int=1, per_page: int=3):
    post_data = await Post.async_first(id=post_id)
    if not post_data:
        return {'r': 1, 'msg': 'Post not exist'}
    
    post = Post(**post_data)
    start = (page - 1) * per_page
    comments = (await post.comments)[start: start + per_page]
    user = await retrieve_user(request)
    print(comments)
    return {
        'r': 0,
        'html': await render_template_def(
            'utils.html', 'render_comments', request,
            {'comments': comments, 'github_user': user, 
              'liked_comment_ids': [] }
        )
    }


@router.post('/markdown')
async def render_markdown(request: Request, text=Form(...)):
    user = await retrieve_user(request)
    if user is None:
        return {'r': 403, 'msg': 'login required'}
    if not text:
        return {'r': 1, 'msg': 'Text required.'}
    return {'r': 0, 'text':  mistune.markdown(text)}
    
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from account.models import Userinfo
from django.urls import reverse


@csrf_exempt
def login(request):
    """
    请求参数
    Body:
    参数名称	    参数类型	是否必须	    示例	    备注
    username	T文本	是	    pawn
    password	T文本	是	    123456

    返回数据
    名称	     类型	是否必须	默认值	备注	其他信息
    code	number	必须
    msg	    string	非必须
    data	object	必须
     - uid	string	必须

    使用账号名和密码进行登录。
    如果登录成功，返回用户信息，通过Set-Cookies返回认证信息
    如果登录失败，code设置为403，不返回data
    """
    user = authenticate(username=request.POST.get('username'),
                        password=request.POST.get('password'))

    if user is not None:
        response_ = JsonResponse({
            'code': 200,
            'data': {
                'uid': user.__str__()
            }
        })
        response_.set_cookie('name',
                             request.POST.get('username'),
                             max_age=3600)
    else:
        response_ = JsonResponse({
            'code': 403,
            'msg': "reason for failing to login"
        })
        response_.status_code = 403
    return response_


@csrf_exempt
def register(request):
    """
    请求参数
    Body:
    参数名称	    参数类型	是否必须	示例	       备注
    username	T文本	是	    user_abcd
    password	T文本	是	    123456abcd

    返回数据
    名称	     类型	是否必须	默认值	备注	其他信息
    code	integer	必须
    msg	    string	非必须

    注册一个账号。
    如果注册成功，正常返回
    如果注册失败，code设置为403，msg为注册失败的原因
    """
    user = Userinfo.objects.create_user(username=request.POST.get('username'),
                                        password=request.POST.get('password'))
    user.save()
    flag = 1
    if flag:
        return HttpResponseRedirect(reverse('account:login'))
    else:
        response_ = JsonResponse({
            'code': 403,
            'msg': "reason for failing to register"
        })
        response_.status_code = 403
        return response_
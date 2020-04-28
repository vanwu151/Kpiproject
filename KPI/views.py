# coding=utf-8
import os, re, time, json
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, HttpResponse
from django.shortcuts import redirect
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum
from .models import userinfo as ui
from .models import kaohe as kh
from .models import score as sc
from .models import kaoheinfo as ki
# Create your views here.


def json_test(request):
    if request.method == "POST":
        a = request.body
        name = json.loads(a)
        print(name)
        jsontest = {"code": "200", "status": "success"}
        jsontest2 = {"ACT": "Hello", "User": name}
        data = [jsontest, jsontest2]
        return JsonResponse(data, safe=False)

def relogin(request):
    if request.method == "GET":
        return render(request, 'Kpi/Login.html')

def register(request):
    try:
        if request.method == "GET":
            return render(request, 'Kpi/register.html')
        elif request.method == "POST":
            user=request.POST.get('user')                                                              #获取前端login页面输入的用户名赋给变量v1
            try:                                                                    
                j = ui.objects.get( user_name = user ).user_name                                       #尝试通过前端login页面获取的用户名从数据库里查询有无记录
                print(j, type(j))
                info = user + ':该用户名已被注册！'                                                      #获取到记录则不会抛出异常，回传给前端Info信息，已查询到相同用户名的用户并提醒该用户名已被注册
                return render(request, 'Kpi/register.html', {'userinfo': {'info': info}})
            except:                                                                                  #如果程序抛出异常则代表前端login页面获取的用户名在已有数据库里未查询到记录
                phone = request.POST.get('phone')                                                      #可继续往下进行用户注册操作
                v5 = request.POST.get('pwd')
                password = make_password(v5,None,'pbkdf2_sha256')
                department = request.POST.get('department')
                info = '恭喜！ ' + user + ' 用户注册成功！'
                q = ui(user_name = user, user_phone = phone, user_password = password, user_department = department)
                q.save()
            return render(request, 'Kpi/Login.html', {'userinfo': {'info': info}})   #注册成功返回到登录页面
    except:
        info = '请填写注册信息！'
        return render(request, 'Kpi/register.html', {'userinfo': {'info': info}})
    
def login(request):
    if request.method == "GET":
        return render(request, 'Kpi/Login.html')

def logout(request):                #注销操作 
    request.session.clear()         #删除session里的全部内容
    return redirect('/login')       #重定向到/login前端页面
    

def logininfo(request):
    if request.method == "POST":
        try:
            UserName=request.POST.get('user')
            UserPass=request.POST.get('pwd')
            # print(UserPass)
            q = ui.objects.get(user_name=UserName)
            name = q.user_name
            pwd  = q.user_password
            print(check_password(UserPass,pwd))
            if UserName == name and check_password(UserPass,pwd) is True:
                request.session['username'] = UserName    #定义session“username”字段并令session中username字段值为登录的用户名
                request.session['is_login'] = True        #定义session“is_login”字段并令该字段值为"True"表示会话已经创建
                todayYearMonth = datetime.today().strftime('%Y-%m')
                kaoheInfoMonth = datetime.strptime(todayYearMonth, '%Y-%m')
                todayYear  = datetime.today().strftime('%Y')         #格式化str格式输出今天是几年
                todayMonth = datetime.today().strftime('%m')         #格式化str格式输出今天是几月
                department = q.user_department
                phone = q.user_phone
                ad = q.user_role
                print(ad , type(ad))
                if ad == 'admin':
                    info = '欢迎您，管理员！'
                    userrole = '管理员'
                    return render(request, 'Kpi/showadmininfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole}})
                if ad == 'manager':
                    info = '欢迎您，部门经理！'
                    userrole = '部门经理'
                    departmentStuff = ui.objects.filter( user_department = department ).exclude( user_name = name )                    
                    try:
                        ki.objects.filter( kaoheinfo_month__year = '{}'.format(todayYear)).filter( kaoheinfo_month__month = '{}'.format(todayMonth)).filter( kaoheinfo_department = department ).filter( kaoheinfo_user = UserName).last() #查看登录的员工当月有无数据
                        # koheinfoMonth = ki.objects.filter( kaoheinfo_department = department ).last().kaoheinfo_month.strftime('%Y-%m')
                        kaoheMonthTargetScore =  ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=name ).last().kaoheinfo_monthtarget   #当月考核目标值
                        kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = UserName ).aggregate(Sum('score_pre'))['score_pre__sum']
                        if kaoheNowScore != None:
                            kaoheNowScore = round( kaoheNowScore/60, 2)
                            fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                            kaoheMonthFiprecent = fi + '%'
                        else:
                            kaoheNowScore = 0   # 如果修改的考核工时不为空或0 计算百分比
                            fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                            kaoheMonthFiprecent = fi + '%'     # 完成百分比为0
                        myStuffList = []
                        myStuffTargetScoreList = []
                        myStuffNowScoreList = []
                        myStuffFiprecentList = []
                        for stuff in departmentStuff:
                            myStuffList.append(stuff.user_name)
                            print(myStuffList)
                            try:
                                myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                            except:
                                myStuffTargetScore = None
                            myStuffTargetScoreList.append(myStuffTargetScore)
                            print(myStuffTargetScoreList)
                            myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if myStuffNowScore != None:
                                myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                try:
                                    myStuffNowScore = round( myStuffNowScore/60, 2)
                                    sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                    myStuffFiprecent = sfi + '%'
                                except:
                                    myStuffFiprecent = '0.0%'
                            else:
                                myStuffNowScore = 0
                                myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                try:
                                    sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                    myStuffFiprecent = sfi + '%'
                                except:
                                    myStuffFiprecent = '0.0%'
                            print(myStuffNowScoreList)
                            myStuffFiprecentList.append(myStuffFiprecent)
                            print(myStuffFiprecentList)
                        stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                        return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent, 'stuffInfoList': stuffInfoList}})
                    except:
                        try:
                            kaoheMonthTargetScore = None
                            kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = UserName ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if kaoheNowScore != None:
                                kaoheNowScore = round( kaoheNowScore/60, 2)    # 如果修改的考核工时不为空或0 计算百分比
                                fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                                kaoheMonthFiprecent = fi + '%'
                            else:
                                kaoheNowScore = 0  
                                fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                                kaoheMonthFiprecent = fi + '%'     # 完成百分比为0
                            myStuffList = []
                            myStuffTargetScoreList = []
                            myStuffNowScoreList = []
                            myStuffFiprecentList = []
                            for stuff in departmentStuff:
                                myStuffList.append(stuff.user_name)
                                try:
                                    myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                                except:
                                    myStuffTargetScore = None
                                myStuffTargetScoreList.append(myStuffTargetScore)
                                myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                                if myStuffNowScore != None:
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                else:
                                    myStuffNowScore = 0
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                if myStuffNowScore != None:
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        myStuffNowScore = round( myStuffNowScore/60, 2)
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                else:
                                    myStuffNowScore = 0
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        myStuffNowScore = round( myStuffNowScore/60, 2)
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                myStuffFiprecentList.append(myStuffFiprecent)
                            stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                            return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent, 'stuffInfoList': stuffInfoList}})
                        except:
                            kaoheMonthTargetScore = None
                            try:
                                kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                                if kaoheNowScore != None:
                                    kaoheNowScore = round( kaoheNowScore/60, 2)
                                else:
                                    kaoheNowScore = None
                                info = '当月还没有考核目标工时！'
                                myStuffList = []
                                myStuffTargetScoreList = []
                                myStuffNowScoreList = []
                                myStuffFiprecentList = []
                                for stuff in departmentStuff:
                                    myStuffList.append(stuff.user_name)
                                    try:
                                        myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                                    except:
                                        myStuffTargetScore = None
                                    myStuffTargetScoreList.append(myStuffTargetScore)
                                    myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                                    if myStuffNowScore != None:
                                        myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                        try:
                                            myStuffNowScore = round( myStuffNowScore/60, 2)
                                            sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                            myStuffFiprecent = sfi + '%'
                                        except:
                                            myStuffFiprecent = '0.0%'
                                    else:
                                        myStuffNowScore = 0
                                        myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                        try:
                                            myStuffNowScore = round( myStuffNowScore/60, 2)
                                            sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                            myStuffFiprecent = sfi + '%'
                                        except:
                                            myStuffFiprecent = '0.0%'
                                    myStuffFiprecentList.append(myStuffFiprecent)
                                stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                                return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'stuffInfoList': stuffInfoList}})
                            except:
                                pass
                else:
                    try:
                        info = '欢迎您：{}'.format(name)
                        kaoheMonthTargetScore =  ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=name ).last().kaoheinfo_monthtarget   #当月考核目标值
                        kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                        if kaoheNowScore != None:
                            kaoheNowScore = round( kaoheNowScore/60, 2)
                            fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                            kaoheMonthFiprecent = fi + '%'
                        else:
                            kaoheNowScore = 0   # 如果考核工时不为空或0 计算百分比
                            fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                            kaoheMonthFiprecent = fi + '%'     # 完成百分比为0
                        return render(request, 'Kpi/showinfo.html', {'userinfo': {'info': info, 'name': name, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent}})
                    except:
                        info = '欢迎您：{}'.format(name)
                        kaoheMonthTargetScore = None
                        try:
                            kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if kaoheNowScore != None:
                                kaoheNowScore = round( kaoheNowScore/60, 2)
                            else:
                                kaoheNowScore = None
                            return render(request, 'Kpi/showinfo.html', {'userinfo': {'info': info, 'name': name, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore}})
                        except:
                            pass

            else:
                info = '用户名或密码错误！'
                return render(request, 'Kpi/Login.html', {'userinfo': {'info': info}})
        except:
            info = '登录信息不能为空！'
            return render(request, 'Kpi/Login.html', {'userinfo': {'info': info}})

def viewinfo(request):
    if request.session.get('is_login',None):
        if request.method == "GET":
            name = request.session['username']
            try:
                q = ui.objects.get( user_name = name )
                ad = q.user_role
                todayYearMonth = datetime.today().strftime('%Y-%m')
                kaoheInfoMonth = datetime.strptime(todayYearMonth, '%Y-%m')
                todayYear  = datetime.today().strftime('%Y')         #格式化str格式输出今天是几年
                todayMonth = datetime.today().strftime('%m')         #格式化str格式输出今天是几月
                department = q.user_department
                phone = q.user_phone
                if ad == 'admin':
                    info = '欢迎您，管理员！'
                    userrole = '管理员'
                    return render(request, 'Kpi/showadmininfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole}})
                if ad == 'manager':
                    info = '欢迎您，部门经理！'
                    userrole = '部门经理'
                    departmentStuff = ui.objects.filter( user_department = department ).exclude( user_name = name ) 
                    try:
                         #查看登录的员工当月有无数据
                        # koheinfoMonth = ki.objects.filter( kaoheinfo_department = department ).last().kaoheinfo_month.strftime('%Y-%m')
                        kaoheMonthTargetScore =  ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=name ).last().kaoheinfo_monthtarget   #当月考核目标值
                        kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                        if kaoheNowScore != None:
                            kaoheNowScore = round( kaoheNowScore/60, 2)
                            fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                            kaoheMonthFiprecent = fi + '%'
                        else:
                            kaoheNowScore = 0   # 如果修改的考核工时不为空或0 计算百分比
                            fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                            kaoheMonthFiprecent = fi + '%'     # 完成百分比为0
                        kiS = ki.objects.filter(kaoheinfo_user = name).last()         #更新kaoheinfo表中的信息
                        kiS.kaoheinfo_monthtotal = kaoheNowScore                      #更新kaoheinfo现有考核时长
                        kiS.kaoheinfo_monthfiprecent = kaoheMonthFiprecent            #更新kaoheinfo目前的考核完成百分比
                        kiS.save()
                        myStuffList = []
                        myStuffTargetScoreList = []
                        myStuffNowScoreList = []
                        myStuffFiprecentList = []
                        for stuff in departmentStuff:
                            myStuffList.append(stuff.user_name)
                            try:
                                myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                            except:
                                myStuffTargetScore = None
                            myStuffTargetScoreList.append(myStuffTargetScore)
                            myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if myStuffNowScore != None:
                                myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                try:
                                    myStuffNowScore = round( myStuffNowScore/60, 2)
                                    sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                    myStuffFiprecent = sfi + '%'
                                except:
                                    myStuffFiprecent = '0.0%'
                            else:
                                myStuffNowScore = 0
                                myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                try:
                                    myStuffNowScore = round( myStuffNowScore/60, 2)
                                    sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                    myStuffFiprecent = sfi + '%'
                                except:
                                    myStuffFiprecent = '0.0%'
                            myStuffFiprecentList.append(myStuffFiprecent)
                        stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                        return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent,'stuffInfoList': stuffInfoList}})
                    except:
                        kaoheMonthTargetScore = None
                        try:
                            kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if kaoheNowScore != None:
                                kaoheNowScore = round( kaoheNowScore/60, 2)
                            else:
                                kaoheNowScore = None
                            info = '当月还没有考核目标工时！'
                            myStuffList = []
                            myStuffTargetScoreList = []
                            myStuffNowScoreList = []
                            myStuffFiprecentList = []
                            for stuff in departmentStuff:
                                myStuffList.append(stuff.user_name)
                                try:
                                    myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                                except:
                                    myStuffTargetScore = None
                                myStuffTargetScoreList.append(myStuffTargetScore)
                                myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                                if myStuffNowScore != None:
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        myStuffNowScore = round( myStuffNowScore/60, 2)
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                else:
                                    myStuffNowScore = 0
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        myStuffNowScore = round( myStuffNowScore/60, 2)
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                myStuffFiprecentList.append(myStuffFiprecent)
                            stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                            return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent, 'stuffInfoList': stuffInfoList}})
                        except:
                            pass
                else:
                    try:
                        info = '欢迎您：{}'.format(name)
                        kaoheMonthTargetScore =  ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=name ).last().kaoheinfo_monthtarget   #当月考核目标值
                        kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                        if kaoheNowScore != None:
                            kaoheNowScore = round( kaoheNowScore/60, 2)
                            fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                            kaoheMonthFiprecent = fi + '%'
                        else:
                            kaoheNowScore = 0   # 如果修改的考核工时不为空或0 计算百分比
                            fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                            kaoheMonthFiprecent = fi + '%'     # 完成百分比为0
                        kiS = ki.objects.filter(kaoheinfo_user = name).last()         #更新kaoheinfo表中的信息
                        kiS.kaoheinfo_monthtotal = kaoheNowScore                      #更新kaoheinfo现有考核时长
                        kiS.kaoheinfo_monthfiprecent = kaoheMonthFiprecent            #更新kaoheinfo目前的考核完成百分比
                        kiS.save()
                        return render(request, 'Kpi/showinfo.html', {'userinfo': {'info': info, 'name': name, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent}})
                    except:
                        info = '欢迎您：{}'.format(name)
                        kaoheMonthTargetScore = None
                        try:
                            kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if kaoheNowScore != None:
                                kaoheNowScore = round( kaoheNowScore/60, 2)
                            else:
                                kaoheNowScore = None
                            return render(request, 'Kpi/showinfo.html', {'userinfo': {'info': info, 'name': name, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore}})
                        except:
                            pass
            except:
                pass

def Editstufftarget(request):
    if request.session.get('is_login',None):
        if request.method == "POST":
            try:
                name = request.session['username']
                q = ui.objects.get( user_name = name )
                ad = q.user_role
                department = q.user_department
                phone = q.user_phone
            except:
                pass
            try:
                action = request.POST.get('action')
                todayYearMonth = datetime.today().strftime('%Y-%m')
                kaoheInfoMonth = datetime.strptime(todayYearMonth, '%Y-%m')
                todayYear  = datetime.today().strftime('%Y')         #格式化str格式输出今天是几年
                todayMonth = datetime.today().strftime('%m')         #格式化str格式输出今天是几月
                departmentStuff = ui.objects.filter( user_department = department ).exclude( user_name = name )      #部门员工清单               
                try:
                    ki.objects.filter( kaoheinfo_month__year = '{}'.format(todayYear)).filter( kaoheinfo_month__month = '{}'.format(todayMonth)).filter( kaoheinfo_department = department ).filter( kaoheinfo_user = name).last() #查看登录的员工当月有无数据
                    # koheinfoMonth = ki.objects.filter( kaoheinfo_department = department ).last().kaoheinfo_month.strftime('%Y-%m')
                    kaoheMonthTargetScore =  ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=name ).last().kaoheinfo_monthtarget   #当月考核目标值
                    kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                    if kaoheNowScore != None:
                        kaoheNowScore = round( kaoheNowScore/60, 2)
                        fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                        kaoheMonthFiprecent = fi + '%'
                    else:
                        kaoheNowScore = 0   # 如果修改的考核工时不为空或0 计算百分比
                        fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                        kaoheMonthFiprecent = fi + '%'     # 完成百分比为0
                except:
                    try:
                        kaoheMonthTargetScore = None
                        kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                        if kaoheNowScore != None:
                            kaoheNowScore = round( kaoheNowScore/60, 2)    # 如果修改的考核工时不为空或0 计算百分比
                            fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                            kaoheMonthFiprecent = fi + '%'
                        else:
                            kaoheNowScore = 0  
                            fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                            kaoheMonthFiprecent = fi + '%'     # 完成百分比为0	
                    except:
                        kaoheMonthTargetScore = None
                        try:
                            kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if kaoheNowScore != None:
                                kaoheNowScore = round( kaoheNowScore/60, 2)
                            else:
                                kaoheNowScore = None
                        except:
                            pass
                if action == "OK":
                    if ad == 'manager':
                        userrole = '部门经理'
                        stuffTargetScore = request.POST.get('stufftarget')
                        print(stuffTargetScore)
                        stuffName = request.POST.get('editstuffname')
                        print(stuffName)
                        if stuffTargetScore != '' or stuffTargetScore != '0':    # 判断目标工时用户填入是否为0或者''空
                            stuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuffName ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if stuffNowScore != None:      # 判断现有工时是否为空，若不为空
                                stuffNowScore = round( stuffNowScore/60, 2)      
                                fi = str(round((stuffNowScore/int(stuffTargetScore)), 2)*100)       # 计算现有工时与目标工时的完成百分比
                                stuffFiprecent = fi + '%'
                            else:                   #若为空
                                stuffNowScore = 0   # 如果修改的考核工时不为空或0 计算百分比
                                fi = str(round((stuffNowScore/int(stuffTargetScore)), 2)*100)       # 计算现有工时与目标工时的完成百分比
                                stuffFiprecent = fi + '%'
                            tki = ki( kaoheinfo_user=stuffName, kaoheinfo_department=department, kaoheinfo_month=kaoheInfoMonth, kaoheinfo_monthtarget=int(stuffTargetScore), kaoheinfo_monthtotal=stuffNowScore, kaoheinfo_monthfiprecent=stuffFiprecent )
                            tki.save()    # 保存 以上的所有信息到kaoheinfo表中
                            info = "{}：{}考核目标已添加！".format(stuffName, todayYearMonth)
                            myStuffList = []
                            myStuffTargetScoreList = []
                            myStuffNowScoreList = []
                            myStuffFiprecentList = []
                            for stuff in departmentStuff:
                                myStuffList.append(stuff.user_name)
                                try:
                                    myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                                except:
                                    myStuffTargetScore = None
                                myStuffTargetScoreList.append(myStuffTargetScore)
                                myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                                if myStuffNowScore != None:
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        myStuffNowScore = round( myStuffNowScore/60, 2)
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                else:
                                    myStuffNowScore = 0
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        myStuffNowScore = round( myStuffNowScore/60, 2)
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                myStuffFiprecentList.append(myStuffFiprecent)
                            stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                            return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent, 'stuffInfoList':stuffInfoList}})
                if action == "修改":
                    if ad == 'manager':
                        userrole = '部门经理'
                        stuffTargetScore = request.POST.get('stufftarget')
                        stuffName = request.POST.get('editstuffname')
                        request.session['edstufftarget'] = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuffName ).last().kaoheinfo_monthtarget   # 将原考核目标时长存入session
                        if stuffTargetScore != '' or stuffTargetScore != '0':    # 判断目标工时用户填入是否为0或者''空
                            stuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuffName ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if stuffNowScore != None:      # 判断现有工时是否为空，若不为空
                                stuffNowScore = round( stuffNowScore/60, 2)      
                                fi = str(round((stuffNowScore/int(stuffTargetScore)), 2)*100)       # 计算现有工时与目标工时的完成百分比
                                stuffFiprecent = fi + '%'
                            else:                   #若为空
                                stuffNowScore = 0   # 如果修改的考核工时不为空或0 计算百分比
                                fi = str(round((stuffNowScore/int(stuffTargetScore)), 2)*100)       # 计算现有工时与目标工时的完成百分比
                                stuffFiprecent = fi + '%'
                            etk = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuffName  ).last()  # 之编辑当前用户当年月的最后一条记录
                            etk.kaoheinfo_monthtarget = int(stuffTargetScore)
                            etk.kaoheinfo_monthtotal = stuffNowScore
                            etk.kaoheinfo_monthfiprecent = stuffFiprecent
                            etk.save()
                            info = "{}：{}考核目标已修改！".format(stuffName, todayYearMonth)
                            myStuffList = []
                            myStuffTargetScoreList = []
                            myStuffNowScoreList = []
                            myStuffFiprecentList = []
                            for stuff in departmentStuff:
                                myStuffList.append(stuff.user_name)
                                try:
                                    myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                                except:
                                    myStuffTargetScore = None
                                myStuffTargetScoreList.append(myStuffTargetScore)
                                myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                                if myStuffNowScore != None:
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        myStuffNowScore = round( myStuffNowScore/60, 2)
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                else:
                                    myStuffNowScore = 0
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        myStuffNowScore = round( myStuffNowScore/60, 2)
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                myStuffFiprecentList.append(myStuffFiprecent)
                            stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                            return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent, 'stuffInfoList': stuffInfoList}})
            except:     # 如果出现目标考核工时为0的异常时
                try:
                    name = request.session['username']
                    q = ui.objects.get( user_name = name )
                    userrole = q.user_role
                    department = q.user_department
                    phone = q.user_phone
                    departmentStuff = ui.objects.filter( user_department = department ).exclude( user_name = name )      #部门员工清单
                except:
                    pass
                try:   
                    myStuffList = []
                    myStuffTargetScoreList = []
                    myStuffNowScoreList = []
                    myStuffFiprecentList = []
                    for stuff in departmentStuff:
                        myStuffList.append(stuff.user_name)
                        try:
                            myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                        except:
                            myStuffTargetScore = None
                        myStuffTargetScoreList.append(myStuffTargetScore)
                        myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                        if myStuffNowScore != None:
                            myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                            try:
                                myStuffNowScore = round( myStuffNowScore/60, 2)
                                sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                myStuffFiprecent = sfi + '%'
                            except:
                                myStuffFiprecent = '0.0%'
                        else:
                            myStuffNowScore = 0
                            myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                            try:
                                myStuffNowScore = round( myStuffNowScore/60, 2)
                                sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                myStuffFiprecent = sfi + '%'
                            except:
                                myStuffFiprecent = '0.0%'
                        myStuffFiprecentList.append(myStuffFiprecent)
                    stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                    info = '目标值不得为空或者0！'
                    return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent, 'stuffInfoList': stuffInfoList}})
                except:
                    pass


def Edittarget(request):
    if request.session.get('is_login',None):
        if request.method == "POST":
            try:
                name = request.session['username']
                q = ui.objects.get( user_name = name )
                ad = q.user_role
                department = q.user_department
                phone = q.user_phone
            except:
                pass
            try:
                action = request.POST.get('action')
                todayYearMonth = datetime.today().strftime('%Y-%m')
                kaoheInfoMonth = datetime.strptime(todayYearMonth, '%Y-%m')
                todayYear  = datetime.today().strftime('%Y')         #格式化str格式输出今天是几年
                todayMonth = datetime.today().strftime('%m')         #格式化str格式输出今天是几月
                departmentStuff = ui.objects.filter( user_department = department ).exclude( user_name = name )      #部门员工清单
                if action == "OK":
                    if ad == 'manager':
                        userrole = '部门经理'
                        kaoheMonthTargetScore = request.POST.get('target')
                        if kaoheMonthTargetScore != '' or kaoheMonthTargetScore != '0':    # 判断目标工时用户填入是否为0或者''空
                            kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if kaoheNowScore != None:      # 判断现有工时是否为空，若不为空
                                kaoheNowScore = round( kaoheNowScore/60, 2)      
                                fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)       # 计算现有工时与目标工时的完成百分比
                                kaoheMonthFiprecent = fi + '%'
                            else:                   #若为空
                                kaoheNowScore = 0   # 如果修改的考核工时不为空或0 计算百分比
                                fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                                kaoheMonthFiprecent = fi + '%'     # 完成百分比为0
                            tki = ki( kaoheinfo_user=name, kaoheinfo_department=department, kaoheinfo_month=kaoheInfoMonth, kaoheinfo_monthtarget=int(kaoheMonthTargetScore), kaoheinfo_monthtotal=kaoheNowScore, kaoheinfo_monthfiprecent=kaoheMonthFiprecent )
                            tki.save()    # 保存 以上的所有信息到kaoheinfo表中
                            info = "{}：{}考核目标已添加！".format(name, todayYearMonth)
                            myStuffList = []
                            myStuffTargetScoreList = []
                            myStuffNowScoreList = []
                            myStuffFiprecentList = []
                            for stuff in departmentStuff:
                                myStuffList.append(stuff.user_name)
                                try:
                                    myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                                except:
                                    myStuffTargetScore = None
                                myStuffTargetScoreList.append(myStuffTargetScore)
                                myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                                if myStuffNowScore != None:
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                else:
                                    myStuffNowScore = 0
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                myStuffFiprecentList.append(myStuffFiprecent)
                            stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                            return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent, 'stuffInfoList':stuffInfoList}})
                if action == "修改":
                    if ad == 'manager':
                        userrole = '部门经理'
                        kaoheMonthTargetScore = request.POST.get('target')
                        request.session['edkhtarget'] = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=name ).last().kaoheinfo_monthtarget   # 将原考核目标时长存入session
                        print(kaoheMonthTargetScore, type(kaoheMonthTargetScore))
                        if kaoheMonthTargetScore != '' or kaoheMonthTargetScore != '0':     # 如果修改的目标考核时长不为空或0
                            kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                            print(kaoheNowScore,type(kaoheNowScore))
                            if kaoheNowScore != None:      # 判断现有工时是否为空，若不为空
                                kaoheNowScore = round( kaoheNowScore/60, 2)      
                                fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)       # 计算现有工时与目标工时的完成百分比
                                kaoheMonthFiprecent = fi + '%'
                            else:                   #若为空
                                kaoheNowScore = 0      # 初始化现有考核时长为0 
                                fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)  #如果修改的考核工时不为空或0 计算百分比
                                kaoheMonthFiprecent = fi + '%'     # 完成百分比为0
                            etk = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=name ).last()  # 之编辑当前用户当年月的最后一条记录
                            etk.kaoheinfo_monthtarget = int(kaoheMonthTargetScore)
                            etk.kaoheinfo_monthtotal = kaoheNowScore
                            etk.kaoheinfo_monthfiprecent = kaoheMonthFiprecent
                            etk.save()
                            info = "{}：{}考核目标已修改！".format(name, todayYearMonth)
                            myStuffList = []
                            myStuffTargetScoreList = []
                            myStuffNowScoreList = []
                            myStuffFiprecentList = []
                            for stuff in departmentStuff:
                                myStuffList.append(stuff.user_name)
                                try:
                                    myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                                except:
                                    myStuffTargetScore = None
                                myStuffTargetScoreList.append(myStuffTargetScore)
                                myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                                if myStuffNowScore != None:
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                else:
                                    myStuffNowScore = 0
                                    myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                    try:
                                        sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                        myStuffFiprecent = sfi + '%'
                                    except:
                                        myStuffFiprecent = '0.0%'
                                myStuffFiprecentList.append(myStuffFiprecent)
                            stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                            return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'kaoheMonthFiprecent': kaoheMonthFiprecent, 'stuffInfoList': stuffInfoList}})
            except:     # 如果出现目标考核工时为0的异常时
                try:
                    departmentStuff = ui.objects.filter( user_department = department ).exclude( user_name = name )      #部门员工清单
                except:
                    pass
                try:   
                    kaoheMonthTargetScore = request.session['edkhtarget']       # 修改目标工时时出现异常,计算百分比时考核目标工时为0抛出异常
                    kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                    if kaoheNowScore != None:
                        kaoheNowScore = round( kaoheNowScore/60, 2)
                    else:
                        kaoheNowScore = None
                    info = '目标值不得为空或者0！'
                    myStuffList = []
                    myStuffTargetScoreList = []
                    myStuffNowScoreList = []
                    myStuffFiprecentList = []
                    for stuff in departmentStuff:
                        myStuffList.append(stuff.user_name)
                        try:
                            myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                        except:
                            myStuffTargetScore = None
                        myStuffTargetScoreList.append(myStuffTargetScore)
                        myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                        if myStuffNowScore != None:
                            myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                            try:
                                sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                myStuffFiprecent = sfi + '%'
                            except:
                                myStuffFiprecent = '0.0%'
                        else:
                            myStuffNowScore = 0
                            myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                            try:
                                sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                myStuffFiprecent = sfi + '%'
                            except:
                                myStuffFiprecent = '0.0%'
                        myStuffFiprecentList.append(myStuffFiprecent)
                    stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                    return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'stuffInfoList': stuffInfoList}})
                except:         # 新增目标工时时出现异常，计算百分比时考核目标工时为0抛出异常
                    kaoheMonthTargetScore = None
                    try:
                        kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = name ).aggregate(Sum('score_pre'))['score_pre__sum']
                        if kaoheNowScore != None:
                            kaoheNowScore = round( kaoheNowScore/60, 2)
                        else:
                            kaoheNowScore = None
                        info = '请填写当月目标不得为空或0！'
                        myStuffList = []
                        myStuffTargetScoreList = []
                        myStuffNowScoreList = []
                        myStuffFiprecentList = []
                        for stuff in departmentStuff:
                            myStuffList.append(stuff.user_name)
                            try:
                                myStuffTargetScore = ki.objects.filter( kaoheinfo_month=kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
                            except:
                                myStuffTargetScore = None
                            myStuffTargetScoreList.append(myStuffTargetScore)
                            myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(todayYear) ).filter( score_datetime__month = '{}'.format(todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
                            if myStuffNowScore != None:
                                myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                try:
                                    sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                    myStuffFiprecent = sfi + '%'
                                except:
                                    myStuffFiprecent = '0.0%'
                            else:
                                myStuffNowScore = 0
                                myStuffNowScoreList.append(round( myStuffNowScore/60, 2))
                                try:
                                    sfi = str(round((myStuffNowScore/int(myStuffTargetScore)), 2)*100)
                                    myStuffFiprecent = sfi + '%'
                                except:
                                    myStuffFiprecent = '0.0%'
                            myStuffFiprecentList.append(myStuffFiprecent)
                        stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
                        return render(request, 'Kpi/showmanagerinfo.html', {'userinfo': {'info': info, 'name': name, 'userrole':userrole, 'department':department, 'phone': phone, 'kaoheMonthTargetScore': kaoheMonthTargetScore, 'kaoheNowScore': kaoheNowScore, 'stuffInfoList': stuffInfoList}})
                    except:
                        pass

def rules(request):
    if request.session.get('is_login',None):
        if request.method == "GET":
            try:
                name = request.session['username']
                q = ui.objects.get( user_name = name )
                department = q.user_department
                test = kh.objects.filter( kaohe_department = department).exists()
                role = q.user_role 
                if test:
                    qkh = kh.objects.all()
                    print(qkh, type(qkh))
                    # print(test)
                    knameList = []
                    kKindList = []
                    kscoreList = []
                    for v1 in qkh:
                        knameList.append(v1.kaohe_name)
                        kKindList.append(v1.kaohe_kind)
                        kscoreList.append(v1.kaohe_score)
                        print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                    kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                    if role == 'manager':
                        return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList}})
                    else:
                        return render(request, 'Kpi/showrulesinfo.html', {'userinfo': {'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList}})
                else:
                    info = '该部门还没有考核规则'
                    if role == 'manager':
                        return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info}})
                    else:
                        return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info}})
            except:
                pass

def AddRules(request):
    if request.session.get('is_login',None):
        if request.method == "POST":
            try:
                name = request.session['username']
                q = ui.objects.get( user_name = name )
                department = q.user_department
                action = request.POST.get('action')
                if action == "新增":
                    kind=request.POST.get('kaohe_kind')
                    print(kind, type(kind))                                                      
                    kaoheName = request.POST.get('kaohe_name')
                    print(kaoheName, type(kaoheName))
                    try:
                        qKaoHeName = kh.objects.get( kaohe_name = kaoheName ).kaohe_name         #考核规则kaohe_name去重
                        info = '考核规则：' + qKaoHeName + '已存在！'
                        print(info)
                        qkh = kh.objects.all()
                        print(qkh, type(qkh))
                        knameList = []
                        kKindList = []
                        kscoreList = []
                        for v1 in qkh:
                            knameList.append(v1.kaohe_name)
                            kKindList.append(v1.kaohe_kind)
                            kscoreList.append(v1.kaohe_score)
                            print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                        kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                        return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'info': info, 'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList}})
                    except:                      
                        kaoheScore = request.POST.get('kaohe_score')
                        print(kaoheScore, type(kaoheScore))
                        if kaoheScore != '':
                            kaoheScore = int(kaoheScore)
                            k = kh(kaohe_name = kaoheName, kaohe_department = department, kaohe_kind = kind, kaohe_score = kaoheScore)
                            k.save()
                        else:
                            k = kh(kaohe_name = kaoheName, kaohe_department = department, kaohe_kind = kind)
                            k.save()
                        info = '新增考核规则：' + kaoheName + '成功'
                        print(info)
                        try:
                            qkh = kh.objects.all()
                            print(qkh, type(qkh))
                            knameList = []
                            kKindList = []
                            kscoreList = []
                            for v1 in qkh:
                                knameList.append(v1.kaohe_name)
                                kKindList.append(v1.kaohe_kind)
                                kscoreList.append(v1.kaohe_score)
                                print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                            kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                            return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'info': info, 'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList}})
                        except:
                            pass
            except:
                pass

def EditRules(request):
    if request.session.get('is_login',None):
        if request.method == "POST":
            try:
                name = request.session['username']
                q = ui.objects.get( user_name = name )
                department = q.user_department
                test = kh.objects.filter( kaohe_department = department).exists()
                if test:
                    action = request.POST.get('action')
                    try:
                        if action == "删除":
                            editkaoheName = request.POST.get('editkaohename')
                            kq = kh.objects.get( kaohe_name = editkaoheName)
                            kq.delete()
                            info = '考核规则：' + editkaoheName + '  已删除'
                            qkh = kh.objects.all()
                            print(qkh, type(qkh))
                            knameList = []
                            kKindList = []
                            kscoreList = []
                            for v1 in qkh:
                                knameList.append(v1.kaohe_name)
                                kKindList.append(v1.kaohe_kind)
                                kscoreList.append(v1.kaohe_score)
                                print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                            kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                            return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList, 'info': info}})
                        if action == "编辑":
                            editkaoheName = request.POST.get('editkaohename')
                            request.session['editkaohename'] = editkaoheName
                            info = '正在编辑考核规则：' + editkaoheName
                            qkh = kh.objects.all()
                            print(qkh, type(qkh))
                            knameList = []
                            kKindList = []
                            kscoreList = []
                            for v1 in qkh:
                                knameList.append(v1.kaohe_name)
                                kKindList.append(v1.kaohe_kind)
                                kscoreList.append(v1.kaohe_score)
                                print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                            kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                            return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList, 'info': info, 'editkaohename': editkaoheName}})
                        if action == "保存":
                            savekind = request.POST.get('kaohe_kind')
                            savename = request.POST.get('kaohe_name')
                            savekaoheScore = request.POST.get('kaohe_score')
                            try:
                                qKaoHeName = kh.objects.get( kaohe_name = savename ).kaohe_name         #考核规则kaohe_name去重
                                print(qKaoHeName)
                                testKaoheRules = kh.objects.filter( kaohe_name = savename ).filter( kaohe_score = savekaoheScore).filter( kaohe_kind = savekind)
                                print(testKaoheRules)
                                try:
                                    testKaoheRules[0]
                                    info = '考核规则：{} 未更改！'.format(savename)
                                    print(info)
                                    qkh = kh.objects.all()
                                    print(qkh, type(qkh))
                                    knameList = []
                                    kKindList = []
                                    kscoreList = []
                                    for v1 in qkh:
                                        knameList.append(v1.kaohe_name)
                                        kKindList.append(v1.kaohe_kind)
                                        kscoreList.append(v1.kaohe_score)
                                        print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                                    kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                                    return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'info': info, 'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList}})
                                except:
                                    try:
                                        edkhname = request.session['editkaohename']
                                        ks = kh.objects.get( kaohe_name = edkhname )
                                        if edkhname != savename and savename == kh.objects.get( kaohe_name = savename ).kaohe_name:    # （确保考核名称唯一性）如果编辑的考核名称和保存的考核名称不相同且保存的考核名称与数据库里的有重名，则重新编辑
                                            info = '考核规则：{} 已存在！请重新编辑 {} ！'.format(savename, edkhname)
                                            print(info)
                                            qkh = kh.objects.all()
                                            print(qkh, type(qkh))
                                            knameList = []
                                            kKindList = []
                                            kscoreList = []
                                            for v1 in qkh:
                                                knameList.append(v1.kaohe_name)
                                                kKindList.append(v1.kaohe_kind)
                                                kscoreList.append(v1.kaohe_score)
                                                print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                                            kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                                            return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'info': info, 'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList}})
                                        else:
                                            if savekaoheScore == '' or savekaoheScore == 'None':
                                                ks.kaohe_kind = savekind
                                                ks.kaohe_score = None
                                                ks.save()
                                                scpre = sc.objects.filter( score_kind = savename )
                                                for v in scpre:
                                                    v.score_pre = None        # 同时更新员工考核事项里的该考核名称工时
                                                    v.save()
                                                    print(v.score_pre)                                                
                                            else:
                                                ks.kaohe_kind = savekind
                                                ks.kaohe_score = int(savekaoheScore)
                                                ks.save()
                                                scpre = sc.objects.filter( score_kind = savename )
                                                for v in scpre:
                                                    v.score_pre = int(savekaoheScore)          # 同时更新员工考核事项里的该考核名称工时
                                                    v.save()
                                            info = '考核规则：{} 已更改！'.format(savename)
                                            print(info)
                                            qkh = kh.objects.all()
                                            print(qkh, type(qkh))
                                            knameList = []
                                            kKindList = []
                                            kscoreList = []
                                            for v1 in qkh:
                                                knameList.append(v1.kaohe_name)
                                                kKindList.append(v1.kaohe_kind)
                                                kscoreList.append(v1.kaohe_score)
                                                print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                                            kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                                            return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'info': info, 'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList}})
                                    except:
                                        pass
                            except:
                                edkhname = request.session['editkaohename']
                                try:
                                    ks = kh.objects.get( kaohe_name = edkhname )
                                    if savekaoheScore == '' or savekaoheScore == 'None':
                                                ks.kaohe_kind = savekind
                                                ks.kaohe_score = None
                                                ks.save()
                                                scpre = sc.objects.filter( score_kind = edkhname )
                                                for v in scpre:
                                                    v.score_pre = None        # 同时更新员工考核事项里的该考核名称工时
                                                    v.save()
                                                    print(v.score_pre)                                                
                                    else:
                                        ks.kaohe_kind = savekind
                                        ks.kaohe_score = int(savekaoheScore)
                                        ks.save()
                                        scpre = sc.objects.filter( score_kind = edkhname )
                                        for v in scpre:
                                            v.score_pre = int(savekaoheScore)        # 同时更新员工考核事项里的该考核名称工时
                                            v.save()
                                            print(v.score_pre)                
                                    info = '考核规则：' + savename + '  已保存'
                                    print(info)
                                    try:
                                        qkh = kh.objects.all()
                                        print(qkh, type(qkh))
                                        knameList = []
                                        kKindList = []
                                        kscoreList = []
                                        for v1 in qkh:
                                            knameList.append(v1.kaohe_name)
                                            kKindList.append(v1.kaohe_kind)
                                            kscoreList.append(v1.kaohe_score)
                                            print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                                        kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                                        return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'info': info, 'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList}})
                                    except:
                                        pass
                                except:
                                    pass
                    except:
                        info = '未勾选考核规则！'
                        try:
                            qkh = kh.objects.all()
                            print(qkh, type(qkh))
                            knameList = []
                            kKindList = []
                            kscoreList = []
                            for v1 in qkh:
                                knameList.append(v1.kaohe_name)
                                kKindList.append(v1.kaohe_kind)
                                kscoreList.append(v1.kaohe_score)
                                print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                            kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                            return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList, 'info': info}})
                        except:
                            pass
                else:
                    info = '该部门还没有考核规则'
                    return render(request, 'Kpi/showkaoherulesinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info}})
            except:
                pass


def managerkaohe(request):
    if request.session.get('is_login',None):
        if request.method == "GET":
            try:
                name = request.session['username']
                q = ui.objects.get( user_name = name )
                department = q.user_department
                roles = q.user_role
                test = sc.objects.filter( score_user = name).exists()
                if roles == 'manager': 
                    if test:
                        qsc = sc.objects.filter( score_user = name ).order_by( 'score_datetime' )
                        print(qsc, type(qsc))
                        # print(test)
                        scidList = []
                        scdateList = []
                        sceventsList = []
                        sckindList = []
                        scpreList = []
                        for v1 in qsc:
                            scidList.append(v1.id)
                            scdateList.append(v1.score_datetime)
                            sceventsList.append(v1.score_events)
                            sckindList.append(v1.score_kind)
                            scpreList.append(v1.score_pre)
                            # print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                        kaohescoresinfoList = zip(scidList, scdateList, sceventsList, sckindList, scpreList)
                        kaohenameKindList = []
                        qkhname = kh.objects.filter( kaohe_department = department )
                        for v2 in qkhname:
                            kaohenameKindList.append(v2.kaohe_name)
                        return render(request, 'Kpi/showmanagerkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList}})
                    else:
                        kaohenameKindList = []
                        info = '还没有考核事项'
                        qkhname = kh.objects.filter( kaohe_department = department )
                        for v2 in qkhname:
                            kaohenameKindList.append(v2.kaohe_name)
                        return render(request, 'Kpi/showmanagerkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info, 'kaohenameKindList': kaohenameKindList}})
                else:
                    if test:
                        qsc = sc.objects.filter( score_user = name ).order_by( 'score_datetime' )
                        print(qsc, type(qsc))
                        # print(test)
                        scidList = []
                        scdateList = []
                        sceventsList = []
                        sckindList = []
                        scpreList = []
                        for v1 in qsc:
                            scidList.append(v1.id)
                            scdateList.append(v1.score_datetime)
                            sceventsList.append(v1.score_events)
                            sckindList.append(v1.score_kind)
                            scpreList.append(v1.score_pre)
                            # print(v1.kaohe_name, v1.kaohe_department, v1.kaohe_kind, v1.kaohe_score)
                        kaohescoresinfoList = zip(scidList, scdateList, sceventsList, sckindList, scpreList)
                        kaohenameKindList = []
                        qkhname = kh.objects.filter( kaohe_department = department )
                        for v2 in qkhname:
                            kaohenameKindList.append(v2.kaohe_name)
                        return render(request, 'Kpi/showkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList}})
                    else:
                        kaohenameKindList = []
                        info = '还没有考核事项'
                        qkhname = kh.objects.filter( kaohe_department = department )
                        for v2 in qkhname:
                            kaohenameKindList.append(v2.kaohe_name)
                        return render(request, 'Kpi/showkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info, 'kaohenameKindList': kaohenameKindList}})
            except:
                pass

def AddEvent(request):
    if request.session.get('is_login',None):
        if request.method == "POST":
            try:
                name = request.session['username']
                q = ui.objects.get( user_name = name )
                department = q.user_department
                action = request.POST.get('action')
                roles = q.user_role
                if action == "新增":
                    eventTime = request.POST.get('date')
                    eventdate = datetime.strptime(eventTime, '%Y-%m-%d')
                    print(eventdate, type(eventdate))                                                      
                    events = request.POST.get('events')
                    print(events, type(events))                     
                    kind = request.POST.get('kind')
                    print(kind, type(kind))
                    pre = kh.objects.get( kaohe_name = kind ).kaohe_score
                    print(pre, type(pre))
                    if pre == None:
                        s = sc(score_user = name, score_datetime = eventdate, score_events = events, score_kind = kind)
                        s.save()
                    else:
                        s = sc(score_user = name, score_datetime = eventdate, score_events = events, score_kind = kind, score_pre = pre)
                        s.save()
                    info = '新增考核事项：' + events + '成功'
                    print(info)
                    try:
                        qsc = sc.objects.filter( score_user = name ).order_by( 'score_datetime' )
                        print(qsc, type(qsc))
                        # print(test)
                        scidList = []
                        scdateList = []
                        sceventsList = []
                        sckindList = []
                        scpreList = []
                        for v1 in qsc:
                            scidList.append(v1.id)
                            scdateList.append(v1.score_datetime)
                            sceventsList.append(v1.score_events)
                            sckindList.append(v1.score_kind)
                            scpreList.append(v1.score_pre)
                        kaohescoresinfoList = zip(scidList, scdateList, sceventsList, sckindList, scpreList)
                        kaohenameKindList = []
                        qkhname = kh.objects.filter( kaohe_department = department )
                        for v2 in qkhname:
                            kaohenameKindList.append(v2.kaohe_name)
                        if roles == 'manager':
                            return render(request, 'Kpi/showmanagerkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList}})
                        else:
                            return render(request, 'Kpi/showkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList}})
                    except:
                        pass
            except:
                pass

def Editevents(request):
    if request.session.get('is_login',None):
        if request.method == "POST":
            try:
                name = request.session['username']
                q = ui.objects.get( user_name = name )
                department = q.user_department
                action = request.POST.get('action')
                roles = q.user_role
                if action == '更新':
                    Editscoreid = request.POST.get('editscoreid')
                    print(Editscoreid, type(Editscoreid))
                    Editpre = request.POST.get('editpre')
                    print(Editpre, type(Editpre))
                    escpre = sc.objects.get(id = Editscoreid)
                    if Editpre == '':
                        info = ''
                        pass
                    else:
                        escpre.score_pre = int(Editpre)
                        escpre.save()
                        info = '自定义考核时长更新成功'
                    print(info)
                    try:
                        qsc = sc.objects.filter( score_user = name ).order_by( 'score_datetime' )
                        print(qsc, type(qsc))
                        # print(test)
                        scidList = []
                        scdateList = []
                        sceventsList = []
                        sckindList = []
                        scpreList = []
                        for v1 in qsc:
                            scidList.append(v1.id)
                            scdateList.append(v1.score_datetime)
                            sceventsList.append(v1.score_events)
                            sckindList.append(v1.score_kind)
                            scpreList.append(v1.score_pre)
                        kaohescoresinfoList = zip(scidList, scdateList, sceventsList, sckindList, scpreList)
                        kaohenameKindList = []
                        qkhname = kh.objects.filter( kaohe_department = department )
                        for v2 in qkhname:
                            kaohenameKindList.append(v2.kaohe_name)
                        if roles == 'manager':
                            return render(request, 'Kpi/showmanagerkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList}})
                        else:
                            return render(request, 'Kpi/showkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList}})
                    except:
                        pass
                if action == '删除':
                    Editscoreid = request.POST.get('editscoreid')
                    print(Editscoreid, type(Editscoreid))
                    sq = sc.objects.get( id = Editscoreid)
                    sq.delete()
                    info = '考核事项已删除'
                    print(info)
                    try:
                        qsc = sc.objects.filter( score_user = name ).order_by( 'score_datetime' )
                        print(qsc, type(qsc))
                        # print(test)
                        scidList = []
                        scdateList = []
                        sceventsList = []
                        sckindList = []
                        scpreList = []
                        for v1 in qsc:
                            scidList.append(v1.id)
                            scdateList.append(v1.score_datetime)
                            sceventsList.append(v1.score_events)
                            sckindList.append(v1.score_kind)
                            scpreList.append(v1.score_pre)
                        kaohescoresinfoList = zip(scidList, scdateList, sceventsList, sckindList, scpreList)
                        kaohenameKindList = []
                        qkhname = kh.objects.filter( kaohe_department = department )
                        for v2 in qkhname:
                            kaohenameKindList.append(v2.kaohe_name)
                        if roles == 'manager':
                            return render(request, 'Kpi/showmanagerkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList}})
                        else:
                            return render(request, 'Kpi/showmanagerkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList}})
                    except:
                        pass
                if action == '编辑':
                    editscoreid = request.POST.get('editscoreid')
                    print(editscoreid, type(editscoreid))
                    request.session['editscoreid'] = editscoreid
                    info = '正在编辑考核事项'
                    try:
                        qsc = sc.objects.filter( score_user = name ).order_by( 'score_datetime' )
                        print(qsc, type(qsc))
                        # print(test)
                        scidList = []
                        scdateList = []
                        sceventsList = []
                        sckindList = []
                        scpreList = []
                        for v1 in qsc:
                            scidList.append(str(v1.id))          # 数据库中的主键id是'int'类型
                            scdateList.append(v1.score_datetime)
                            sceventsList.append(v1.score_events)
                            sckindList.append(v1.score_kind)
                            scpreList.append(v1.score_pre)
                        kaohescoresinfoList = zip(scidList, scdateList, sceventsList, sckindList, scpreList)
                        kaohenameKindList = []
                        qkhname = kh.objects.filter( kaohe_department = department )
                        for v2 in qkhname:
                            kaohenameKindList.append(v2.kaohe_name)
                        if roles == 'manager':
                            return render(request, 'Kpi/showmanagerkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList, 'editscoreid': editscoreid}})
                        else:
                            return render(request, 'Kpi/showkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList, 'editscoreid': editscoreid}})
                    except:
                        pass
                if action == '保存':
                    saveTime = request.POST.get('date')
                    saveDate = datetime.strptime(saveTime, '%Y-%m-%d')
                    saveEvents = request.POST.get('events')
                    saveNamekind = request.POST.get('kind')
                    savePre = kh.objects.get( kaohe_name = saveNamekind ).kaohe_score
                    try:
                        saveid = request.session['editscoreid']
                        print(saveid, type(saveid)) 
                        savesc = sc.objects.get( id = saveid )
                        savesc.score_datetime = saveDate
                        savesc.score_events = saveEvents
                        savesc.score_kind = saveNamekind
                        savesc.score_pre = savePre
                        savesc.save()
                        info = '考核事项已更改！'
                        try:
                            qsc = sc.objects.filter( score_user = name ).order_by( 'score_datetime' )
                            print(qsc, type(qsc))
                            # print(test)
                            scidList = []
                            scdateList = []
                            sceventsList = []
                            sckindList = []
                            scpreList = []
                            for v1 in qsc:
                                scidList.append(v1.id)
                                scdateList.append(v1.score_datetime)
                                sceventsList.append(v1.score_events)
                                sckindList.append(v1.score_kind)
                                scpreList.append(v1.score_pre)
                            kaohescoresinfoList = zip(scidList, scdateList, sceventsList, sckindList, scpreList)
                            kaohenameKindList = []
                            qkhname = kh.objects.filter( kaohe_department = department )
                            for v2 in qkhname:
                                kaohenameKindList.append(v2.kaohe_name)
                            if roles == 'manager':
                                return render(request, 'Kpi/showmanagerkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList}})
                            else:
                                return render(request, 'Kpi/showkaoheinfo.html', {'userinfo': {'name': name, 'department': department, 'info': info, 'kaohescoresinfoList': kaohescoresinfoList, 'kaohenameKindList': kaohenameKindList}})
                        except:
                            pass
                    except:
                        pass
            except:
                pass

def Manage(request):
    if request.session.get('is_login',None):
        if request.method == "POST" or request.method == "GET":
            try:
                # info = '用户管理列表'
                m = request.session['username']
                userdic = ui.objects.exclude(user_name = m).exclude(user_name = "admin")
                userlist = []
                rolelist = []
                for i in userdic:
                    userlist.append(i)
                print(userlist)
                for k in userlist:
                    q = ui.objects.get(user_name = k)
                    role = q.user_role
                    rolelist.append(role)
                print(rolelist)
                userroleinfolist=zip(userlist,rolelist)                    #将userlist与rolelist打包成userroleinfolist
                return render(request, 'Kpi/Manage.html', {'userinfo': {'name': m, 'userroleinfolist': userroleinfolist}})
            except:
                pass

def Edit(request):
    if request.session.get('is_login',None):
        if request.method == "POST":
            EditUserName = request.POST.get('username')
            request.session['EditUserName'] = EditUserName                              #定义session“EditUserName”字段并令session中EditUserName字段值为需要编辑的用户名
            print(EditUserName)
            action = request.POST.get('action')
            try:
                try:
                    if action == "编辑":
                        q = ui.objects.get(user_name = EditUserName)
                        phone = q.user_phone
                        department = q.user_department
                        userrole = q.user_role
                        return render(request, 'Kpi/Edituserinfo.html', {'userinfo': {'name': request.session['username'], 'editusername': EditUserName,'phone': phone,'department': department, 'userrole':userrole}})
                except:
                    info = '请勾选需要编辑的用户'            # 未勾选用户名点编辑后的报错提醒
                    m = request.session['username']
                    try:
                        userdic = ui.objects.exclude(user_name = m).exclude(user_name = "admin")
                        userlist = []
                        rolelist = []
                        for i in userdic:
                            userlist.append(i)
                        print(userlist)
                        for k in userlist:
                            q = ui.objects.get(user_name = k)
                            role = q.user_role
                            rolelist.append(role)
                        print(rolelist)
                        userroleinfolist=zip(userlist,rolelist)
                    except:
                        pass
                    return render(request, 'Kpi/Manage.html', {'userinfo': {'info': info, 'name':m, 'userroleinfolist': userroleinfolist}})
                try:
                    if action == "删除":
                        q = ui.objects.get(user_name = EditUserName)
                        q.delete()
                        return redirect('/Manage')
                except:
                    info = '请勾选需要删除的用户'            # 未勾选用户名点编辑后的报错提醒
                    m = request.session['username']
                    try:
                        userdic = ui.objects.exclude(user_name = m).exclude(user_name = "admin")
                        userlist = []
                        rolelist = []
                        for i in userdic:
                            userlist.append(i)
                        print(userlist)
                        for k in userlist:
                            q = ui.objects.get(user_name = k)
                            role = q.user_role
                            rolelist.append(role)
                        print(rolelist)
                        userroleinfolist=zip(userlist,rolelist)
                    except:
                        pass
                    return render(request, 'Kpi/Manage.html', {'userinfo': {'info': info, 'name':m, 'userroleinfolist': userroleinfolist}})
            except:
                pass

def ModRole(request):
    if request.session.get('is_login',None):
        if request.method == "POST":
            try:
                Moduser = request.session['EditUserName']
                print(Moduser)
                q = ui.objects.get(user_name = Moduser)
                Moddepartment = request.POST.get('department')
                Modrole = request.POST.get('role')
                if Moddepartment is not None:
                    q.user_department = Moddepartment
                    q.save()
                else:
                    pass
                if Modrole is not None:    
                    q.user_role = Modrole
                    q.save()
                else:
                    pass
                ModNewPass = request.POST.get('newpass') 
                if ModNewPass != '':
                    NewUserPass = make_password(ModNewPass, None, 'pbkdf2_sha256')
                    q.user_password = NewUserPass
                    q.save()
                    info = Moduser + '密码已更改!'
                else:
                    info = Moduser + '密码未更改!'    
                    pass
                if Modrole is None and ModNewPass == '':
                    info = Moduser + '信息未更改!'    
                name = q.user_name
                phone = q.user_phone
                department = q.user_department
                userrole = q.user_role
                return render(request, 'Kpi/Edituserinfo.html', {'userinfo': {'info': info, 'name': request.session['username'], 'editusername': name,'phone': phone,'department': department, 'userrole':userrole}})
            except:
                pass

def Modinfo(request):
    if request.session.get('is_login',None):
        if request.method == "GET":
            name = request.session['username']
            try:
                department = ui.objects.get( user_name = name).user_department
                phone = ui.objects.get( user_name = name ).user_phone
            except:
                pass
            return render(request, 'Kpi/Modinfo.html', {'userinfo': {'name': name, 'phone': phone, 'department': department}})


def InfoModed(request):
    if request.session.get('is_login',None):
        if request.method == "POST":        
            try:
                m = request.session['username']     #从session中获取用户姓名
                p = request.POST.get('passwd')      #获取前端输入的密码赋给变量p
                q = ui.objects.get(user_name=m)     #以查询条件q：字段user_name值为cookie重保存的用户信息为条件
                department = q.user_department
                phone = q.user_phone
                p2 = q.user_password                #通过查询条件q将用户的密码赋给变量p2
                if check_password(p,p2) is True:                               #当输入的密码p和查询出的密码p2比较后为真       
                    info = m + '信息更改成功！'
                    name = q.user_name                                         #将回传给前端的name字段赋值为通过查询条件q查到的用户名
                    ModPwd = request.POST.get('userinfo_passwd')
                    if ModPwd != '':
                        NewPwd = make_password(ModPwd ,None, 'pbkdf2_sha256')
                        q.user_password = NewPwd
                        q.save()
                        info = m + '密码已更改！'
                    else:
                        pass
                    ModPhone = request.POST.get('phone')
                    if ModPhone != '':                                      #如果获取到的新昵称值不是空的
                        q.user_nickname = ModPhone                          #则将变量ModPhon新号码，更新到数据库user_phone字段
                        q.save()                                               #保存更新
                        phone = q.user_phone                             #将回传给前端的user_phone字段赋值为通过查询条件q查到的昵称
                    else:                                                      #如果获取到的新昵称是空的
                        phone = q.phone                             #则不去更新数据库
                    return render(request, 'Kpi/Modinfo.html', {'userinfo': {'info': info, 'name': name, 'phone': phone, 'department': department}})
                elif check_password(p,p2) is False:
                    info = '密码错误！信息更改失败！'
                    name = q.user_name
                    return render(request, 'Kpi/Modinfo.html', {'userinfo': {'info': info, 'name': name, 'phone': phone, 'department': department}})
                else:
                    info = '用户信息错误！信息更改失败！'
                    name = q.user_name
                    return render(request, 'Kpi/Modinfo.html', {'userinfo': {'info': info, 'name': name, 'phone': phone, 'department': department}})
            except:
                info = '请填入正确的修改信息！'
                name = q.user_name
                return render(request, 'Kpi/Modinfo.html', {'userinfo': {'info': info, 'name': name, 'phone': phone, 'department': department}})






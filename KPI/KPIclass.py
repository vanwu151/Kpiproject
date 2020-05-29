import os, re, time, json
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum
from .models import userinfo as ui
from .models import kaohe as kh
from .models import score as sc
from .models import kaoheinfo as ki


class showUserInfo:
    '''
    回传普通用户考核基本信息数据

    '''
    def __init__(self, info, name, kaoheInfoMonth, department, todayYear, todayMonth, phone):
        self.info = info
        self.name = name
        self.kaoheInfoMonth = kaoheInfoMonth
        self.department = department
        self.todayYear = todayYear
        self.todayMonth = todayMonth
        self.phone = phone

    def getUserInfoData(self):
        try:
            # info = '欢迎您：{}'.format(self.name)
            kaoheMonthTargetScore =  ki.objects.filter( kaoheinfo_month=self.kaoheInfoMonth ).filter( kaoheinfo_user=self.name ).filter( kaoheinfo_department = self.department ).last().kaoheinfo_monthtarget   #当月考核目标值
            print('当月考核工时：{}'.format(kaoheMonthTargetScore))
            kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(self.todayYear) ).filter( score_datetime__month = '{}'.format(self.todayMonth)).filter( score_user = self.name ).aggregate(Sum('score_pre'))['score_pre__sum']
            if kaoheNowScore != None:
                kaoheNowScore = round( kaoheNowScore/60, 2)
                fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                kaoheMonthFiprecent = fi + '%'
            else:
                kaoheNowScore = 0   # 如果修改的考核工时不为空或0 计算百分比
                fi = str(round((kaoheNowScore/int(kaoheMonthTargetScore)), 2)*100)
                kaoheMonthFiprecent = fi + '%'     # 完成百分比为0
            kiS = ki.objects.filter(kaoheinfo_user = self.name).last()         #更新kaoheinfo表中的信息
            kiS.kaoheinfo_monthtotal = kaoheNowScore                      #更新kaoheinfo现有考核时长
            kiS.kaoheinfo_department = self.department
            kiS.kaoheinfo_monthfiprecent = kaoheMonthFiprecent            #更新kaoheinfo目前的考核完成百分比
            kiS.save()
            userInfoData =  {'userinfo': {'info': self.info, 
                                 'name': self.name, 
                                 'department':self.department, 
                                 'phone': self.phone, 
                                 'kaoheMonthTargetScore': kaoheMonthTargetScore, 
                                 'kaoheNowScore': kaoheNowScore, 
                                 'kaoheMonthFiprecent': kaoheMonthFiprecent}}
        except:
            kaoheMonthTargetScore = None
            kaoheMonthFiprecent = None
            print('当月考核工时：{}'.format(kaoheMonthTargetScore))
            try:
                kaoheNowScore = sc.objects.filter( score_datetime__year = '{}'.format(self.todayYear) ).filter( score_datetime__month = '{}'.format(self.todayMonth)).filter( score_user = self.name ).aggregate(Sum('score_pre'))['score_pre__sum']
                kaoheNowScore = round( kaoheNowScore/60, 2)
            except:
                kaoheNowScore = None
                print('现有考核工时：{}'.format(kaoheNowScore))
            userInfoData =  {'userinfo': {'info': self.info, 
                                     'name': self.name, 
                                     'department':self.department, 
                                     'phone': self.phone, 
                                     'kaoheMonthTargetScore': kaoheMonthTargetScore, 
                                     'kaoheNowScore': kaoheNowScore, 
                                     'kaoheMonthFiprecent': kaoheMonthFiprecent}}
        return userInfoData

class showManagerInfo(showUserInfo):
    '''
    回传经理级用户考核基本信息数据

    '''
    def __init__(self, departmentStuff, userrole, info, name, kaoheInfoMonth, department, todayYear, todayMonth, phone):
        showUserInfo.__init__(self, info, name, kaoheInfoMonth, department, todayYear, todayMonth, phone)
        self.departmentStuff = departmentStuff
        self.userrole = userrole

    def getManagerInfoData(self):
        managerInfoData = showUserInfo.getUserInfoData(self)
        managerInfoData['userinfo']['userrole'] = self.userrole
        myStuffList = []
        myStuffTargetScoreList = []
        myStuffNowScoreList = []
        myStuffFiprecentList = []
        for stuff in self.departmentStuff:
            myStuffList.append(stuff.user_name)
            try:
                myStuffTargetScore = ki.objects.filter( kaoheinfo_month=self.kaoheInfoMonth ).filter( kaoheinfo_user=stuff.user_name ).last().kaoheinfo_monthtarget
            except:
                myStuffTargetScore = None
            try:
                myStuffTargetScoreList.append(myStuffTargetScore)
                myStuffNowScore = sc.objects.filter( score_datetime__year = '{}'.format(self.todayYear) ).filter( score_datetime__month = '{}'.format(self.todayMonth)).filter( score_user = stuff.user_name ).aggregate(Sum('score_pre'))['score_pre__sum']
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
            except:
                pass
        stuffInfoList = zip(myStuffList, myStuffTargetScoreList, myStuffNowScoreList, myStuffFiprecentList)
        managerInfoData['userinfo']['stuffInfoList'] = stuffInfoList
        return managerInfoData


class getKpiRules:
    '''
    回传普通用户考核规则信息数据

    '''
    def __init__(self, name):
        self.name = name

    def getKpiRulesData(self):
        try:
            q = ui.objects.get( user_name = self.name )
            department = q.user_department
            test = kh.objects.filter( kaohe_department = department).exists()
            role = q.user_role 
            if test:
                qkh = kh.objects.all()
                knameList = []
                kKindList = []
                kscoreList = []
                for v1 in qkh:
                    knameList.append(v1.kaohe_name)
                    kKindList.append(v1.kaohe_kind)
                    kscoreList.append(v1.kaohe_score)
                kaoherulesinfoList = zip(knameList, kKindList, kscoreList)
                kpiRUlesData = {'userinfo':{'name': self.name, 
                                    'role': role,
                                    'department': department, 
                                    'kaoherulesinfoList': kaoherulesinfoList}}  #  {'userinfo': {'name': name, 'department': department, 'kaoherulesinfoList': kaoherulesinfoList, 'info': info}}                                    
            else:
                info = '该部门还没有考核规则'
                kpiRUlesData = {'userinfo':{'info': info, 
                                    'role': role,
                                    'name': self.name, 
                                    'department':department}}
        except:
            pass
        print(kpiRUlesData)
        return kpiRUlesData



class getAddedRules(getKpiRules):
    '''
    回传新增考核规则后的信息数据

    '''
    def __init__(self, name, **kwds):
        getKpiRules.__init__(self, name)
        self.kind = kwds['kind']
        self.kaoheName = kwds['kaoheName']
        self.kaoheScore = kwds['kaoheScore']
        self.department = kwds['department']

    def getAddedRulesData(self):
        try:
            qKaoHeName = kh.objects.get( kaohe_name = self.kaoheName ).kaohe_name         #考核规则kaohe_name去重
            info = '考核规则：' + qKaoHeName + '已存在！'
            print(info)
        except:
            if self.kaoheScore != '':
                kaoheScore = int(self.kaoheScore)
                k = kh(kaohe_name = self.kaoheName, kaohe_department = self.department, kaohe_kind = self.kind, kaohe_score = kaoheScore)
                k.save()
            else:
                k = kh(kaohe_name = self.kaoheName, kaohe_department = self.department, kaohe_kind = self.kind)
                k.save()
            info = '新增考核规则：' + self.kaoheName + '成功'
            print(info)
        AddedRulesDataView = getKpiRules(self.name)
        AddedRulesData = AddedRulesDataView.getKpiRulesData()
        AddedRulesData['userinfo']['info'] = info
        print(AddedRulesData)
        return AddedRulesData



class getEditedRules(getAddedRules):
    '''
    回传修改考核规则后的信息数据

    '''
    def __init__(self, name, **kwds):
        getKpiRules.__init__(self, name)
        try:
            self.kind = kwds['kind']
        except:
            pass
        try:
            self.kaoheName = kwds['kaoheName']
        except:
            pass
        try:
            self.kaoheScore = kwds['kaoheScore']
        except:
            pass
        try:
            self.department = kwds['department']
        except:
            pass
        try:
            self.editkaoheName = kwds['editkaoheName']
        except:
            pass

    def getDeledRulesData(self):
        try:
            kq = kh.objects.get( kaohe_name = self.editkaoheName)
            kq.delete()
        except:
            pass
        info = '考核规则：' +self.editkaoheName + '  已删除'
        DeledRulesDataView = getKpiRules(self.name)
        DeledRulesData = DeledRulesDataView.getKpiRulesData()
        DeledRulesData['userinfo']['info'] = info
        return DeledRulesData

    def getEditedRulesData(self):
        info = '正在编辑考核规则：' + self.editkaoheName
        EditedRulesDataView = getKpiRules(self.name)
        EditedRulesData = EditedRulesDataView.getKpiRulesData()
        EditedRulesData['userinfo']['info'] = info
        EditedRulesData['userinfo']['editkaohename'] = self.editkaoheName
        return EditedRulesData

    def getSavedRulesData(self):
        try:
            kh.objects.get( kaohe_name = self.kaoheName ).kaohe_name         #考核规则kaohe_name去重
            testKaoheRules = kh.objects.filter( kaohe_name = self.kaoheName ).filter( kaohe_score = self.kaoheScore).filter( kaohe_kind = self.kind)
            try:
                testKaoheRules[0]
                info = '考核规则：{} 未更改！'.format(self.kaoheName)
                print(info)
            except:
                try:
                    ks = kh.objects.get( kaohe_name = self.editkaoheName )
                    if self.editkaoheName != self.kaoheName and self.kaoheName == kh.objects.get( kaohe_name = self.kaoheName ).kaohe_name:    # （确保考核名称唯一性）如果编辑的考核名称和保存的考核名称不相同且保存的考核名称与数据库里的有重名，则重新编辑
                        info = '考核规则：{} 已存在！请重新编辑 {} ！'.format(self.kaoheName, self.editkaoheName)
                        print(info)
                    else:
                        if self.kaoheScore == '' or self.kaoheScore == 'None':
                            ks.kaohe_kind = self.kind
                            ks.kaohe_score = None
                            ks.save()
                            scpre = sc.objects.filter( score_kind = self.kaoheName )
                            for v in scpre:
                                v.score_pre = None        # 同时更新员工考核事项里的该考核名称工时
                                v.save()                                                
                        else:
                            ks.kaohe_kind = self.kind
                            ks.kaohe_score = int(self.kaoheScore)
                            ks.save()
                            scpre = sc.objects.filter( score_kind = self.kaoheName )
                            for v in scpre:
                                v.score_pre = int(self.kaoheScore)          # 同时更新员工考核事项里的该考核名称工时
                                v.save()
                        info = '考核规则：{} 已更改！'.format(self.kaoheName)
                        print(info)
                except:
                    pass
        except:
            try:
                ks = kh.objects.get( kaohe_name = self.editkaoheName )
                if self.kaoheScore == '' or self.kaoheScore == 'None':
                    ks.kaohe_name = self.kaoheName
                    ks.kaohe_kind = self.kind
                    ks.kaohe_score = None
                    ks.save()
                    scpre = sc.objects.filter( score_kind = self.editkaoheName )
                    for v in scpre:
                        v.score_pre = None        # 同时更新员工考核事项里的该考核名称工时
                        v.score_kind = self.kaoheName   # 同时更新员工考核事项里的该考核的种类名称
                        v.save()                                               
                else:
                    ks.kaohe_name = self.kaoheName
                    ks.kaohe_kind = self.kind
                    ks.kaohe_score = int(self.kaoheScore)
                    ks.save()
                    scpre = sc.objects.filter( score_kind = self.editkaoheName )
                    for v in scpre:
                        v.score_pre = int(self.kaoheScore)          # 同时更新员工考核事项里的该考核名称工时
                        v.score_kind = self.kaoheName   # 同时更新员工考核事项里的该考核的种类名称
                        v.save()
                info = '考核规则：{} 已保存！'.format(self.kaoheName)
                print(info)
            except:
                pass
        savedRulesDataView = getKpiRules(self.name)
        savedRulesData = savedRulesDataView.getKpiRulesData()
        savedRulesData['userinfo']['info'] = info
        print(savedRulesData)
        return savedRulesData



class getUserScore:
    """
    回传用户考核分数详情

    """
    def __init__(self, name, **kwds):
        self.name = name

    def getUserScoreData(self):
        try:
            q = ui.objects.get( user_name = self.name )
            department = q.user_department
            roles = q.user_role
            test = sc.objects.filter( score_user = self.name).exists()
            if test:
                qsc = sc.objects.filter( score_user = self.name ).order_by( '-score_datetime' )
                scidList = []
                scdateList = []
                sceventsList = []
                sckindList = []
                scpreList = []
                screquiredepartmentlist = []
                screquireusernamelist = []
                for v1 in qsc:
                    scidList.append(v1.id)
                    scdateList.append(v1.score_datetime)
                    sceventsList.append(v1.score_events)
                    sckindList.append(v1.score_kind)
                    scpreList.append(v1.score_pre)
                    screquiredepartmentlist.append(v1.score_require_department)
                    screquireusernamelist.append(v1.score_require_username)
                kaohescoresinfoList = zip(scidList, scdateList, sceventsList, sckindList, scpreList, screquiredepartmentlist, screquireusernamelist)
                kaohenameKindList = []
                qkhname = kh.objects.filter( kaohe_department = department )
                for v2 in qkhname:
                    kaohenameKindList.append(v2.kaohe_name)
                UserScoreData = {'userinfo': {'name': self.name,
                                 'roles': roles, 
                                 'department': department, 
                                 'kaohescoresinfoList': kaohescoresinfoList, 
                                 'kaohenameKindList': kaohenameKindList}}
            else:
                kaohenameKindList = []
                info = '还没有考核事项'
                qkhname = kh.objects.filter( kaohe_department = department )
                for v2 in qkhname:
                    kaohenameKindList.append(v2.kaohe_name)
                UserScoreData['userinfo']['info'] = info
        except:
            print('here2')
            pass
        return UserScoreData


class getAddedUserScore(getUserScore):
    """
    回传用户增加考核事项分数详情

    """
    def __init__(self, name, **kwds):
        getUserScore.__init__(self, name)
        self.eventTime = kwds['eventTime']
        self.events = kwds['events']
        self.kind = kwds['kind']
        self.requireDepartment = kwds['requireDepartment']
        self.requireUsername = kwds['requireUsername']

    def getAddedUserScoreData(self):
        eventdate = datetime.strptime(self.eventTime, '%Y-%m-%d')
        try:
            pre = kh.objects.get( kaohe_name = self.kind ).kaohe_score
        except:
            pass
        if pre == None:
            s = sc(score_user = self.name, score_datetime = eventdate, score_events = self.events, score_kind = self.kind, score_require_department = self.requireDepartment, score_require_username = self.requireUsername)
            s.save()
        else:
            s = sc(score_user = self.name, score_datetime = eventdate, score_events = self.events, score_kind = self.kind, score_pre = pre, score_require_department = self.requireDepartment, score_require_username = self.requireUsername)
            s.save()
        info = '新增考核事项：' + self.events + '成功'
        getAddedUserScoreView = getUserScore(self.name)
        getAddedUserScoreData = getAddedUserScoreView.getUserScoreData()
        getAddedUserScoreData['userinfo']['info'] = info
        return getAddedUserScoreData


class getEditedUserScore(getUserScore):
    """
    回传用户修改考核事项分数详情

    """
    def __init__(self, name, **kwds):
        getUserScore.__init__(self, name)
        try:
            self.Editscoreid = kwds['Editscoreid']
        except:
            pass
        try:
            self.Editpre  = kwds['Editpre']
        except:
            pass
        try:
            self.saveTime = kwds['saveTime']
        except:
            pass
        try:
            self.events = kwds['events']
        except:
            pass
        try:
            self.kind = kwds['kind']
        except:
            pass
        try:
            self.requireDepartment = kwds['requireDepartment']
        except:
            pass
        try:
            self.requireUsername = kwds['requireUsername']
        except:
            pass


    def getUpdatedUserScore(self):
        try:
            escpre = sc.objects.get(id = self.Editscoreid)
        except:
            pass
        Editpre = self.Editpre
        if Editpre == '':
            info = ''
            pass
        else:
            escpre.score_pre = int(Editpre)
            escpre.save()
            info = '自定义考核时长更新成功'
        getUpdatedUserScoreView = getUserScore(self.name)
        getUpdatedUserScoreData = getUpdatedUserScoreView.getUserScoreData()
        getUpdatedUserScoreData['userinfo']['info'] = info
        return getUpdatedUserScoreData

    def getDeledUserScore(self):
        try:
            sq = sc.objects.get( id = self.Editscoreid)
            sq.delete()
        except:
            pass
        info = '考核事项已删除'
        getDeledUserScoreView = getUserScore(self.name)
        getDeledUserScoreData = getDeledUserScoreView.getUserScoreData()
        getDeledUserScoreData['userinfo']['info'] = info
        return getDeledUserScoreData

    def getEditingUserScore(self):
        info = '正在编辑考核事项'
        editscoreid = self.Editscoreid
        getEditingUserScoreView = getUserScore(self.name)
        getEditingUserScoreData = getEditingUserScoreView.getUserScoreData()
        getEditingUserScoreData['userinfo']['info'] = info
        getEditingUserScoreData['userinfo']['editscoreid'] = int(editscoreid)   # 数据库中的主键id是'int'类型
        return getEditingUserScoreData

    def getSavedUserScore(self):
        saveDate = datetime.strptime(self.saveTime, '%Y-%m-%d')
        try:
            savePre = kh.objects.get( kaohe_name = self.kind ).kaohe_score
            saveEvents = self.events
            saveNamekind = self.kind
            saveid = self.Editscoreid
            saveReqDepartment = self.requireDepartment
            saveReqUsername = self.requireUsername
            print(saveid, type(saveid)) 
            savesc = sc.objects.get( id = saveid )
            savesc.score_datetime = saveDate
            savesc.score_events = saveEvents
            savesc.score_kind = saveNamekind
            savesc.score_pre = savePre
            savesc.score_require_department = saveReqDepartment
            savesc.score_require_username = saveReqUsername
            savesc.save()
        except:
            pass
        info = '考核事项已更改！'
        getSavedUserScoreView = getUserScore(self.name)
        getSavedUserScoreData = getSavedUserScoreView.getUserScoreData()
        getSavedUserScoreData['userinfo']['info'] = info
        return getSavedUserScoreData



    






from django.db import models
import django.utils.timezone as timezone
import datetime
# Create your models here.

class userinfo(models.Model):
	user_name = models.CharField(max_length=20)
	user_phone = models.CharField(max_length=20, default="")
	# user_sex = models.CharField(max_length=20)
	# user_city = models.CharField(max_length=20)
	user_department = models.CharField(max_length=50)
	# user_hobby = models.CharField(max_length=200)
	user_password = models.CharField(max_length=128, default="")
	user_role = models.CharField(max_length=20, default="")
	user_manager = models.CharField(max_length=20, default="")
	
	def __str__(self):
		return self.user_name

class kaoheinfo(models.Model):
	kaoheinfo_user = models.CharField(max_length=20)
	kaoheinfo_department = models.CharField(max_length=20)
	kaoheinfo_month = models.DateTimeField('更新时间', default=timezone.now)
	kaoheinfo_monthtarget = models.IntegerField(blank=True, null=True)
	kaoheinfo_monthtotal = models.IntegerField(blank=True, null=True)
	kaoheinfo_monthfiprecent = models.CharField(max_length=20)


class kaohe(models.Model):
	kaohe_name = models.CharField(max_length=500)
	kaohe_department = models.CharField(max_length=20, default="")
	kaohe_kind = models.CharField(max_length=100)
	kaohe_score = models.IntegerField(blank=True, null=True)

	def __str__(self):
		return self.kaohe_name

class score(models.Model):
	score_user = models.CharField(max_length=20)
	score_datetime = models.DateTimeField('更新时间', default=timezone.now)
	score_require_department = models.CharField(max_length=20, default="")
	score_require_username = models.CharField(max_length=20, default="")
	score_events = models.CharField(max_length=500)
	score_kind = models.CharField(max_length=100)
	score_pre = models.IntegerField(blank=True, null=True)

	def __str__(self):
		return self.score_user
#upload.objects.exlude(user_name='admin')
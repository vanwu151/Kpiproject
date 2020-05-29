# class SchoolMember:
#     '''代表任何学校里的成员。'''

#     def __init__(self, name, age):
#         self.name = name
#         self.age = age
#         print('(初始化 SchoolMember: {})'.format(self.name))

#     def tell(self):
#         '''输出对象信息'''
#         memberinfodata = { 'memberinfo': {'name': self.name, 'age': self.age}}
#         print(memberinfodata)
#         return memberinfodata

# class Teacher(SchoolMember):
#     '''代表一位老师。'''

#     def __init__(self, name, age, salary):
#         SchoolMember.__init__(self, name, age)
#         self.salary = salary 
#         print('(初始化 Teacher: {})'.format(self.name))

#     def tell(self):
#         memberinfodata = SchoolMember.tell(self)
#         memberinfodata['memberinfo']['salary'] = self.salary 
#         print(memberinfodata)
#         return memberinfodata


# class Student(SchoolMember):
#     '''代表一位学生。'''

#     def __init__(self, name, age, marks):
#         SchoolMember.__init__(self,    name, age)
#         self.marks = marks 
#         print('(初始化 Student: {})'.format(self.name))

#     def tell(self):
#         memberinfodata = SchoolMember.tell(self)
#         memberinfodata['memberinfo']['marks'] = self.marks  
#         print(memberinfodata)
#         return memberinfodata


# if __name__ == "__main__":
#     print('初始化过程：')
#     t = Teacher('张老师', 40, 10000)
#     s = Student('李四', 25, 75)

#     print('\n对象调用方法：')
#     t.tell()
#     s.tell()


def infolist(**kwargs):
    list1 = []
    for k,v in kwargs.items():
        dic = {k: v}
        list1.append(dic)
    return list1

if __name__ == "__main__":
    name = input('姓名：')
    age = input('年龄：')
    sex = input('性别：')
    city = input('城市：')
    k = infolist(name = name, age = age, sex = sex, city =city)
    print(k)

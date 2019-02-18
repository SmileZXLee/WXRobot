#coding=utf-8
import mysql.connector
import requests
import itchat
import time
import json
import os
from itchat.content import *
KEY = ''
rec_msg_dict = {}
rec_tmp_dir = os.path.join(os.getcwd(), 'tmp/')
#数据库配置
def db_conn():
    mydb = mysql.connector.connect(
        host="localhost",       # 数据库主机地址
        user="root",    # 数据库用户名
        passwd="123456",   # 数据库密码
        database="wxrobot" # 数据库
    )
    return mydb
mydb = db_conn()
#数据库table模型
class wxrobot:
    msg_type = ''
    msg_time = ''
    msg_content = ''
    msg_sender = ''
    msg_receiver = ''
    msg_sender_name = ''
    msg_receiver_name = ''
    is_at = 0
    is_group = 0
    msg_group = ''
    msg_group_name = ''
    def __init__(self,type,time,content,sender,receiver,sender_name,receiver_name,is_at,is_group,group,group_name):
        self.msg_type = type
        self.msg_time = time
        self.msg_content = content
        self.msg_sender = sender
        self.msg_receiver = receiver
        self.msg_sender_name = sender_name
        self.msg_receiver_name = receiver_name
        self.is_at = is_at
        self.is_group = is_group
        self.msg_group = group
        self.msg_group_name = group_name

#数据库操作
def insert_db(r):
    sql = "INSERT INTO wxrobot (msg_type,msg_time,msg_content,msg_sender,msg_receiver,msg_sender_name,msg_receiver_name,is_at,is_group,msg_group,msg_group_name) VALUES (%s, %s,%s, %s,%s, %s,%s, %s, %s,%s, %s)"
    val = (r.msg_type, r.msg_time,r.msg_content,r.msg_sender,r.msg_receiver,r.msg_sender_name,r.msg_receiver_name,r.is_at,r.is_group,r.msg_group,r.msg_group_name)
    #mydb = db_conn()
    mycursor = mydb.cursor()
    mycursor.execute(sql, val)
    mydb.commit()
    return mycursor.rowcount  

#机器人登录成功
def after_login():
    print('微信机器人登录成功')
    # global mycursor
    mydb = db_conn()

#机器人退出登录
def after_logout():
    print('微信机器人退出成功')
#消息处理部分
def deal_rep_msg(msg):
    msg_id = msg['MsgId']
    msg_from_user = msg['FromUserName']
    msg_from_user_name = msg['User']['NickName'] if u'NickName' in msg['User'] else msg['User']['UserName'];
    msg_content = ''
    # 收到信息的时间
    msg_time_rec = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    msg_create_time = msg['CreateTime']
    msg_type = msg['Type']
    msg_group = msg_from_user
    msg_group_name = msg_from_user_name
    if msg['Type'] == 'Text':
        msg_content = msg['Content']
    elif msg['Type'] == 'Picture' \
            or msg['Type'] == 'Recording' \
            or msg['Type'] == 'Video' \
            or msg['Type'] == 'Attachment':
        msg_content = r"" + msg['FileName']
        msg['Text'](rec_tmp_dir + msg['FileName'])
    rec_msg_dict.update({
        'msg_id' : msg_id,
        'msg_from_user': msg_from_user,
        'msg_time_rec': msg_time_rec,
        'msg_create_time': msg_create_time,
        'msg_type': msg_type,
        'msg_content': msg_content,
        'msg_from_user_name': msg_from_user_name,
        'msg_group' : msg_group,
        'msg_group_name' : msg_group_name
    })
    return rec_msg_dict;

#图灵机器人测试部分-------------------------------
def get_response(msg):

    apiUrl = 'http://www.tuling123.com/openapi/api'
    data = {
        'key'    : KEY,
        'info'   : msg,
        'userid' : 'wechat-robot',
    }
    try:
        r = requests.post(apiUrl, data=data).json()

        return r.get('text')

    except:

        return


@itchat.msg_register(itchat.content.TEXT)
def tuling_reply(msg):

    defaultReply = 'I received: ' + msg['Text']

    reply = get_response(msg['Text'])

    return reply or defaultReply


#查找用户---------------------------------------
@itchat.msg_register(itchat.content.TEXT)
def look_up_reply(msg):
    flag = msg['Text'].split()[0]
    if(len(msg['Text'].split() > 1)): 
        look_up_info = msg['Text'].split()[1]
        print(look_up_info)
        if (flag == u'查找'):
            result = itchat.search_friends(name=look_up_info)
            print(result)
            return 1


#主动发送信息-----------------------------------
#通过昵称获取用户真实userName
def get_real_user_name(name):
    user_info = itchat.search_friends(name=name)
    if (len(user_info) > 0):
        return user_info[0]['UserName']
    else:
        return ''      
#通过昵称发送信息
def send_friend_msg(name,msg):
    real_user_name = get_real_user_name(name);
    if(len(real_user_name)):
        itchat.send_msg(msg, get_real_user_name(name))
        itchat.send_image('test.jpg', get_real_user_name(name))
    else:
        print('找不到这个好友')
@itchat.msg_register([TEXT, PICTURE, RECORDING, ATTACHMENT, VIDEO], isFriendChat=True , isGroupChat=False)
def send_msg_test(msg):
    #print(json.dumps(msg))
    deal_rep = deal_rep_msg(msg)
    msg_time1 = deal_rep['msg_time_rec']
    nick_name =  deal_rep['msg_from_user_name']
    content = deal_rep['msg_content']
    from_user = deal_rep['msg_from_user']
    print(msg_time1 +u' [好友消息]'+nick_name+u'说:'+content)
    r = wxrobot(deal_rep['msg_type'],msg_time1,content,from_user,itchat.search_friends()['UserName'],nick_name,itchat.search_friends()['NickName'],0,0,'','')
    insert_db(r)

#群聊部分------------------------------------------
#通过群昵称获取真实chatName
def get_real_chat_room(name):
    chat_rooms = itchat.search_chatrooms(name=name)
    if (len(chat_rooms) > 0):
        return chat_rooms[0]['UserName']
    else:
        return ''
#通过群昵称发送信息
def send_chat_room_msg(name,msg):
    real_chat_room = get_real_chat_room(name);
    if(len(real_chat_room)):
        itchat.send_msg(msg, get_real_chat_room(name))
    else:
        print('找不到这个群')
@itchat.msg_register([TEXT, PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True)
def reply_msg(msg):
    #print(msg)
    deal_rep = deal_rep_msg(msg)
    msg_time = deal_rep['msg_time_rec']
    #print(json.dumps(msg))
    nick_name = deal_rep['msg_from_user_name']
    content = deal_rep['msg_content']
    from_user = deal_rep['msg_from_user']
    r = wxrobot(deal_rep['msg_type'],msg_time,content,from_user,itchat.search_friends()['UserName'],msg['ActualNickName'],itchat.search_friends()['NickName'],msg['isAt'],1,deal_rep['msg_group'],deal_rep['msg_group_name'])
    insert_db(r)
    print(msg_time +u' [群消息]'+msg['ActualNickName']+u'在群'+nick_name+u'中说:'+content)



itchat.auto_login(hotReload=True,loginCallback=after_login, exitCallback=after_logout)
itchat.run()

from flask import Flask,request,render_template,redirect,url_for,session,flash,Response
from flask_session import Session
from otp import genotp
import bcrypt
from stoken import token,dtoken
from cmail import send_mail
import mysql.connector
import os
import re
import pdfkit
import razorpay
app=Flask(__name__)
#config=pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
app.config['SESSION_TYPE']='filesystem'
RAZORPAY_KEY_ID='rzp_test_RXy19zNlFo9p8F'
RAZORPAY_KEY_SECRET='eIHxmEyJqhKz2l0tHEy7KkkC'
client=razorpay.Client(auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET))
app.secret_key=b'\xd8\x0f\xc5]#\x88Jxe\xd9'
Session(app)
#mydb=mysql.connector.connect(host='localhost',user='root',password='Admin',db='ecommy')
user=os.environ.get('RDS_USERNAME')
db=os.environ.get('RDS_DB_NAME')
password=os.environ.get('RDS_PASSWORD')
host=os.environ.get('RDS_HOSTNAME')
port=os.environ.get('RDS_PORT')
with mysql.connector.connect(host=host,port=port,db=db,user=user,password=password) as conn:
    cursor=conn.cursor()
    cursor.execute("CREATE TABLE if not exists user (user_name varchar(100) DEFAULT NULL,user_id int NOT NULL AUTO_INCREMENT,email varchar(30) DEFAULT NULL,password varbinary(200) DEFAULT NULL,address tinytext NOT NULL,gender enum('male','female') DEFAULT NULL,PRIMARY KEY (user_id),UNIQUE KEY email (email))")
    cursor.execute("CREATE TABLE if not exists admin (admin_name varchar(100) NOT NULL,email varchar(30) NOT NULL,password varchar(100) DEFAULT NULL,address tinytext,admin_id int NOT NULL AUTO_INCREMENT,image_name varchar(100) DEFAULT NULL,PRIMARY KEY (admin_id),UNIQUE KEY email (email))")
    cursor.execute("CREATE TABLE if not exists orders (ord_id bigint NOT NULL AUTO_INCREMENT,item_name longtext,qyt int DEFAULT NULL,total_price bigint DEFAULT NULL,user int DEFAULT NULL,itemid binary(16) DEFAULT NULL,PRIMARY KEY (ord_id),KEY user (user),KEY items_od (itemid),CONSTRAINT items_od FOREIGN KEY (itemid) REFERENCES items (itemid) ON DELETE SET NULL,CONSTRAINT orders_ibfk_2 FOREIGN KEY (user) REFERENCES user (user_id))")
    cursor.execute("CREATE TABLE if not exists items (itemid binary(16) NOT NULL,item_name longtext NOT NULL,description longtext NOT NULL,category enum('electronics','home','fashion','grocery') DEFAULT NULL,price bigint DEFAULT NULL,quantity int DEFAULT NULL,image_name varchar(10) NOT NULL,added_by int DEFAULT NULL,PRIMARY KEY (itemid),KEY added_by (added_by),CONSTRAINT items_ibfk_1 FOREIGN KEY (added_by) REFERENCES admin (admin_id))")
    cursor.execute("CREATE TABLE if not exists review (r_id int NOT NULL AUTO_INCREMENT,review_text text,itemid binary(16) DEFAULT NULL,added_by int DEFAULT NULL,created_at datetime DEFAULT CURRENT_TIMESTAMP,rating enum('1','2','3','4','5') NOT NULL,title text NOT NULL,PRIMARY KEY (r_id),KEY itemid (itemid),KEY added_by (added_by),CONSTRAINT review_ibfk_1 FOREIGN KEY (itemid) REFERENCES items (itemid),CONSTRAINT review_ibfk_2 FOREIGN KEY (added_by) REFERENCES user (user_id))")
mydb=mysql.connector.connect(host=host,user=user,port=port,password=password,db=db)
@app.route('/')
def welcome():
    return render_template('welcome.html')
@app.route('/welcomeadmin')
def welcomeadmin():
    return render_template('welcomeadmin.html')
@app.route('/welcomeuser')
def welcomeuser():
    return render_template('welcomeuser.html')
@app.route('/admin_signup',methods=['GET','POST'])
def admin_signup():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        address=request.form['address']
        image=request.files['img']
        imgname=image.filename
        imgname=genotp()+'.'+image.filename.split('.')[-1]
        path=os.path.dirname(os.path.abspath(__file__)) #C:\Users\Kittu\OneDrive\Desktop\Documents\Sri-flask\ecom
        static_path=os.path.join(path,'static') #C:\Users\Kittu\OneDrive\Desktop\Documents\Sri-flask\ecom\static
        image.save(os.path.join(static_path,imgname)) #C:\Users\Kittu\OneDrive\Desktop\Documents\Sri-flask\ecom\static\Gt5Hy3
        cursor=mydb.cursor(buffered=True)
        cursor.execute('Select count(*) from admin where email=%s',[email])
        countdata=cursor.fetchone()
        if countdata:
            if countdata[0]==0:
                otp=genotp()
                data={'username':username,'address':address,'email':email,'password':password,'imgname':imgname,'otp':otp}
                subject='Admin Registeration OTP For Ecom App'
                body=f'OTP For Admin Register {otp}'
                send_mail(to=email,subject=subject,body=body)
                return redirect(url_for('adminverify',regdata=token(data=data)))
            elif countdata[0]==1:
                flash('Email already exsisted')
                return redirect(url_for('alogin'))
        else:
            return 'Something went wrong'
    return render_template('adminsignup.html')
@app.route('/adminverify/<regdata>',methods=['GET','POST'])
def adminverify(regdata):
    try:
        data=dtoken(data=regdata)
    except Exception as e:
        print(e)
        return 'Something Went Wrong'
    else:
        if request.method=='POST':
            uotp=request.form['notp']
            if uotp==data['otp']:
                try: 
                    bytes=data['password'].encode('utf-8')
                    salt=bcrypt.gensalt()
                    hash=bcrypt.hashpw(bytes,salt)
                    print(hash)
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('insert into admin(admin_name,email,password,address,image_name) values(%s,%s,%s,%s,%s)',[data['username'],data['email'],hash,data['address'],data['imgname']])
                    mydb.commit()
                    cursor.close()
                    return redirect(url_for('alogin'))
                except Exception as e:
                    print(e)
                    return 'Error'
            else:
                return 'OTP Wrong'
    return render_template('otp.html')
@app.route('/user_signup',methods=['GET','POST'])
def user_signup():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        address=request.form['address']
        gender=request.form['gender']
        otp=genotp()
        data={'username':username,'address':address,'email':email,'password':password,'otp':otp,'gender':gender}
        subject='User Registeration OTP For Ecom App'
        body=f'OTP For User Register {otp}'
        send_mail(to=email,subject=subject,body=body)
        return redirect(url_for('userverify',regdata=token(data)))
    return render_template('usersignup.html')
@app.route('/userverify/<regdata>',methods=['GET','POST'])
def userverify(regdata):
    try:
        data=dtoken(data=regdata)
    except Exception as e:
        print(e)
        return 'Something Went Wrong'
    else:
        if request.method=='POST':
            uotp=request.form['motp']
            if uotp==data['otp']:
                try: 
                    bytes=data['password'].encode('utf-8')
                    salt=bcrypt.gensalt()
                    hash=bcrypt.hashpw(bytes,salt)
                    print(hash)
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('insert into user(user_name,email,password,address,gender) values(%s,%s,%s,%s,%s)',[data['username'],data['email'],hash,data['address'],data['gender']])
                    mydb.commit()
                    cursor.close()
                    return redirect(url_for('ulogin'))
                except Exception as e:
                    print(e)
                    return 'Error'
            else:
                return 'OTP Wrong'
    return render_template('userotp.html')
@app.route('/ulogin',methods=['GET','POST'])
def ulogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        cursor = mydb.cursor(buffered=True)
        cursor.execute('Select count(*) from user where email = %s', [email])
        counts = cursor.fetchone()
        if counts:
            if counts[0] == 1:
                cursor.execute('Select password from user where email = %s', [email])
                npassword = cursor.fetchone()[0]
                print(npassword)
                if bcrypt.checkpw(password, npassword):
                    session['user'] = email
                    if not session.get('email'):
                        session[email] = {}
                    return redirect(url_for('panel'))
                else:
                    flash('Password was incorrect')
                    return redirect(url_for('ulogin'))
            flash('Email not found. Please try again')
            return redirect(url_for('ulogin'))
        return 'Something went wrong'
    return render_template('ulogin.html')
@app.route('/alogin',methods=['GET','POST'])
def alogin():
    if not session.get('admin'):
        if request.method=='POST':
            email=request.form['email']
            password=request.form['password'].encode('utf-8')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('Select count(*) from admin where email=%s',[email])
            countdata=cursor.fetchone()
            if countdata:
                if countdata[0]==1:
                    cursor.execute('Select password from admin where email=%s',[email])
                    spassword=cursor.fetchone()[0].encode('utf-8')
                    print(spassword)
                    if bcrypt.checkpw(password,spassword):
                        session['admin']=email
                        if not session.get('email'):
                            session[email]={}
                        return redirect(url_for('admindashboard'))
                    else:
                        flash('Password was incorrect')
                        return redirect(url_for('alogin'))
                flash('Email not found.Please try again')
                return redirect(url_for('alogin'))
            return 'Something went wrong'
        return render_template('alogin.html')
    return redirect(url_for('admindashboard'))
@app.route('/admindashboard')
def admindashboard():
    if session.get('admin'):
        return render_template('admindashboard.html')
    return redirect(url_for('alogin'))
@app.route('/additem',methods=['GET','POST'])
def additem():
    if session.get('admin'):
        if request.method=='POST':
            title=request.form['title']
            description=request.form['desc']
            quantity=request.form['quan']
            price=request.form['price']
            category=request.form['category']
            img=request.files['img']
            imgname=genotp()+'.'+img.filename.split('.')[-1]
            path=os.path.dirname(os.path.abspath(__file__))
            static_path=os.path.join(path,'static')
            img.save(os.path.join(static_path,imgname))
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('Select admin_id from admin where email=%s',[session.get('admin')])
                ad_id=cursor.fetchone()
                if ad_id:
                    cursor.execute('Insert into items(itemid, item_name, description, price, quantity, image_name, category, added_by) values (uuid_to_bin(uuid()), %s, %s, %s, %s,%s, %s, %s)',
                    [title, description, price, quantity, imgname, category, ad_id[0]])
                    mydb.commit()
                    cursor.close()
                    flash(f'Item {title} added successfully')
                    return redirect(url_for('additem'))
                else:
                    return 'Please login again something went wrong'
            except Exception as e:
                print(e)
                return 'Something went wrong'
        return render_template('additem.html')
    return redirect(url_for('alogin'))
@app.route('/viewitems')
def viewitems():
    if session.get('admin'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('Select admin_id from admin where email=%s',[session.get('admin')])
        ad_id=cursor.fetchone()
        if ad_id:
            cursor.execute('Select bin_to_uuid(itemid),item_name,image_name from items where added_by=%s',[ad_id[0]])
            itemsdata=cursor.fetchall()
            if itemsdata:
                return render_template('cards.html',itemsdata=itemsdata)
            else:
                return 'No items found'
        else:
            return 'User id not found'   
    return redirect(url_for('alogin'))
@app.route('/view_item/<itemid>')
def view_item(itemid):
    if session.get('admin'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('Select admin_id from admin where email=%s',[session.get('admin')])
        ad_id=cursor.fetchone()
        if ad_id:
            cursor.execute('Select bin_to_uuid(itemid), item_name, description, price, quantity, image_name, category, added_by from items where added_by=%s and itemid=uuid_to_bin(%s)',[ad_id[0],itemid])
            item_data=cursor.fetchone()
            if item_data:
                return render_template('viewallitems.html',item_data=item_data)
            else:
                return 'No item found'
        else:
            return 'User id not found'
    return redirect(url_for('alogin'))
@app.route('/update/<itemid>',methods=['GET','POST'])
def update(itemid):
    if session.get('admin'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('Select admin_id from admin where email=%s',[session.get('admin')])
        ad_id=cursor.fetchone()
        if ad_id:
            cursor.execute('Select bin_to_uuid(itemid), item_name, description, price, quantity, image_name, category, added_by from items where added_by=%s and itemid=uuid_to_bin(%s)',[ad_id[0],itemid])
            item_data=cursor.fetchone()
            if request.method=='POST':
                title=request.form['title']
                description=request.form['desc']
                quantity=request.form['quan']
                price=request.form['price']
                category=request.form['category']
                img=request.files['img']
                if img.filename=='':
                    imgname=item_data[5]
                else:
                    imgname=genotp()+'.'+img.filename.split('.')[-1]
                    path=os.path.dirname(os.path.abspath(__file__))
                    static_path=os.path.join(path,'static')
                    os.remove(os.path.join(static_path,item_data[5]))
                    img.save(os.path.join(static_path,imgname))
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update items set item_name=%s,description=%s, price=%s, quantity=%s, image_name=%s, category=%s where itemid=uuid_to_bin(%s)',[title,description,price,quantity,imgname,category,itemid])
                mydb.commit()
                cursor.close()
                flash(f'Items {title} Updated Successfully')
                return redirect(url_for('update',itemid=itemid))
            if item_data:
                return render_template('update.html',item_data=item_data)
            else:
                return 'No item found'
        return 'User id not found'
    return redirect(url_for('alogin'))
@app.route('/delete/<itemid>')
def delete(itemid):
    if session.get('admin'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('Select admin_id from admin where email=%s',[session.get('admin')])
        ad_id=cursor.fetchone()
        if ad_id:
            cursor.execute('Select image_name from items where itemid=uuid_to_bin(%s)',[itemid])
            imgdata=cursor.fetchone()[0]
            path=os.path.dirname(os.path.abspath(__file__))
            static_path=os.path.join(path,'static')
            # os.remove(os.path.join(static_path,imgdata))
            cursor.execute('Delete from review where itemid=uuid_to_bin(%s)',[itemid])
            cursor.execute('Delete from items where itemid=uuid_to_bin(%s) and added_by=%s',[itemid,ad_id[0]])
            mydb.commit()
            cursor.close()
            flash(f'Item deleted successfully')
            return redirect(url_for('viewitems'))
        else:
            return 'User not found'
    return redirect(url_for('alogin')) 
@app.route('/adminlogout') 
def adminlogout():
    if session.get('admin'):
        session.pop('admin')
        return redirect(url_for('alogin'))
    else:
        return redirect(url_for('alogin'))
@app.route('/panel',methods=['GET','POST'])
def panel():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('Select bin_to_uuid(itemid),item_name,image_name,price from items')
    itemsdata=cursor.fetchall()
    return render_template('panel.html',itemsdata=itemsdata)
@app.route('/dashboard/<ctype>')
def dashboard(ctype):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from items where category=%s',[ctype])
    data=cursor.fetchall()
    return render_template('dashboard.html',data=data)
@app.route('/description/<itemid>')
def description(itemid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select bin_to_uuid(itemid),item_name,description,category,price,quantity,image_name,added_by from items where itemid=uuid_to_bin(%s)',[itemid])
    data=cursor.fetchone()
    return render_template('description.html',data=data)
@app.route('/addreview/<itemid>',methods=['GET','POST'])
def addreview(itemid):
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            review=request.form['review']
            rating=request.form['rate']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('Select user_id from user where email=%s',[session.get('user')])
            u_id=cursor.fetchone()[0]
            cursor.execute('Insert into review (title,review_text,rating,itemid,added_by) values(%s,%s,%s,uuid_to_bin(%s),%s)',[title,review,rating,itemid,u_id])
            mydb.commit()
            cursor.close()
            flash('Review added successfully')
            return redirect(url_for('description',itemid=itemid))
        return render_template('review.html')
    return redirect(url_for('ulogin'))
@app.route('/addcart/<itemid>')
def addcart(itemid):
    if session.get('user'):
        print(session)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('Select bin_to_uuid(itemid),item_name,description,category,price,quantity,image_name,added_by from items where itemid=uuid_to_bin(%s)',[itemid])
        data=cursor.fetchone()
        item_name=data[1]
        category=data[3]
        price=data[4]
        if request.method=='POST':
            quantity=request.form['qyt']
        else:
            quantity=1
        image=data[6]
        if itemid not in session['user']:
            session[session.get('user')][itemid]=[item_name,price,quantity,image,category]
            session.modified=True
            print(session)
            flash(f'{item_name} added_to cart')
            return redirect(url_for('panel'))
        session[session.get('user')][itemid][2]=+1
        flash('Item already existed')
        return redirect(url_for('panel'))
    return redirect(url_for('ulogin'))
@app.route('/viewcart')
def viewcart():
    if session.get('user'):
        if session.get(session.get('user')):
            items=session[session.get('user')]
            print(items)
            return render_template('cart.html',items=items)
        else:
            items='Empty'
        if items=='Empty':
            return 'No products added'
    return redirect(url_for('ulogin'))
@app.route('/removecart/<itemid>')
def removecart(itemid):
    if session.get('user'):
        session[session.get('user')].pop(itemid)
        session.modified=True
        return redirect(url_for('panel'))
    return redirect(url_for('ulogin'))
@app.route('/readreview/<itemid>')
def readreview(itemid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('Select bin_to_uuid(itemid),item_name,description,category,price,quantity,image_name from items where itemid=uuid_to_bin(%s)',[itemid])
    data1=cursor.fetchone()
    cursor.execute('Select * from review where itemid=uuid_to_bin(%s)',[itemid])
    data2=cursor.fetchall()
    data=list(data1)+data2
    print(data)
    return render_template('description.html',data=data,data2=data2)
@app.route('/pay/<itemid>/<name>/<int:price>',methods=['GET','POST'])
def pay(itemid,name,price):
    if session.get('user'):
        try:
            if request.method=='POST':
                qyt=int(request.form['qyt'])
            else:
                qyt=1
            total_price=price*qyt
            print(price,qyt,total_price)
            print(f'Creating payment for item:{itemid},name:{name},price:{total_price}')
            #Creating RazorPay Order
            order=client.order.create({
                'amount':total_price * 100,
                'currency':'INR',
                'payment_capture':'1'
            })
            print(f'Order created:{order}')
            return render_template('pay.html',order=order,itemid=itemid,name=name,price=total_price,qyt=qyt)
        except Exception as e:
            print(e)
            return str(e),400
    return redirect('ulogin')
@app.route('/success',methods=['POST'])
def success():
    #extra payments details from the form
    payment_id=request.form.get('razorpay_payment_id')
    order_id=request.form.get('razorpay_order_id')
    signature=request.form.get('razorpay_signature')
    name=request.form['name']
    itemid=request.form['itemid']
    total_price=request.form['total_price']
    qyt=request.form['qyt']
    param_dict={
        'razorpay_payment_id':payment_id,
        'razorpay_order_id':order_id,
        'razorpay_signature':signature
    }
    try:
        client.utility.verify_payment_signature(param_dict)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('Select user_id from user where email=%s',[session.get('user')])
        u_id=cursor.fetchone()[0]
        cursor.execute('Insert into orders(itemid,item_name,total_price,user,qyt) values (uuid_to_bin(%s),%s,%s,%s,%s)',[itemid,name,total_price,u_id,qyt])
        mydb.commit()
        cursor.close()
        flash('Order placed successfully')
        return redirect(url_for('orders'))
    except Exception as e:
        print(e)
        return f'{e}',400
@app.route('/orders')
def orders():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('Select user_id from user where email=%s',[session.get('user')])
        u_id=cursor.fetchone()
        cursor.execute('Select * from orders where user=%s',[u_id[0]])
        users_orders=cursor.fetchall()
        cursor.close()
        return render_template('orders.html',users_orders=users_orders)
    return redirect(url_for('ulogin'))
@app.route('/search',methods=['GET','POST'])
def search():
    if request.method=='POST':
        name=request.form['search']
        strg=['A-Za-z0-9']
        pattern=re.compile(f'{strg}',re.IGNORECASE)
        if (pattern.match(name)):
            cursor=mydb.cursor(buffered=True)
            query='Select bin_to_uuid(itemid),item_name,description,category,price,quantity,image_name from items where item_name like %s or price like %s or description like %s or category like %s or quantity like %s'
            search_pram=f'%{name}%'
            cursor.execute(query,[search_pram,search_pram,search_pram,search_pram,search_pram])
            data=cursor.fetchall()
            return render_template('dashboard.html',data=data)
        else:
            flash('Result not found')
    return render_template('panel.html')
# @app.route('/billdetails/<ordid>.pdf')
# def billdetails(ordid):
#     if session.get('user'):
#         cursor=mydb.cursor(buffered=True)
#         cursor.execute('Select * from orders where ord_id=%s',[ordid])
#         orders=cursor.fetchone()
#         userid=orders[4]
#         oname=orders[1]
#         qyt=orders[2]
#         cost=orders[3]
#         cursor.execute('Select user_name,address,email from user where user_id=%s',[orders[4]])
#         data=cursor.fetchone()
#         uname=data[0]
#         address=data[1]
#         email=data[2]
#         html=render_template('bill.html',uname=uname,address=address,oname=oname,qyt=qyt,cost=cost,email=email)
#         pdf=pdfkit.from_string(html,False,configuration=config)
#         response=Response(pdf,content_type='application/pdf')
#         response.headers['Content-Disposition']='inline; filename=output.pdf'
#         return response
if __name__=='__main__':
    app.run()
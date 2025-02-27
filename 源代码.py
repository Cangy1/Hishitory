#导入模块
import sys   #system访问变量和函数
import sqlite3  #SQLite数据库
import hashlib  #哈希库
import re  #正则表达式
import os  #与操作系统交互（用相对路径显示开屏动画）
from PyQt5.QtWidgets import *    #*表示导入所有模块
from PyQt5.QtCore import *
from PyQt5.QtGui import *

show_main_window = False
current_dir = os.path.dirname(os.path.realpath(__file__))  #获取当前工作目录
resources_dir = os.path.join(current_dir, 'resources')  #设置资源文件夹的相对路径
logo_path = os.path.join(resources_dir, 'logo.png')  #使用相对路径设置Logo

#设置开屏动画
class SplashScreen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        #设置窗口属性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)  #放在最顶层
        self.setAttribute(Qt.WA_TranslucentBackground)  #窗口图片不显示的时候是透明的
        self.setSizeGripEnabled(False)

        #添加 Logo 标签
        self.setModal(False)
        logo_label = QLabel(self)
        logo_label.setPixmap(QPixmap(logo_path).scaled(800, 800, Qt.KeepAspectRatio))

        #设置布局
        layout = QVBoxLayout()
        layout.addWidget(logo_label)
        self.setLayout(layout)

        #设置窗口大小和位置
        self.resize(800, 800)  #Logo 大小
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())#logo居中

        #启动画面显示时长
        self.show()
        QTimer.singleShot(3000, self.close)  # 3秒后关闭启动画面

    def closeEvent(self, event):
        #当启动画面关闭时，设置全局变量为 True，用来控制主窗口的显示
        global show_main_window
        show_main_window = True
        super().closeEvent(event)

class DiaryApp(QMainWindow):
    #初始化
    def __init__(self):
        super().__init__()
        self.user_logged_in = False
        self.current_user_id = None
        self.initUI()
        self.db_connection = self.create_connection()
        self.create_user_table()  #确保用户表存在
        self.create_diaries_table()  #创建日记表，确保这个表存在

    #初始化用户界面
    def initUI(self):
        #设置窗口标题和大小
        self.setWindowTitle("Hishitory 史记")
        app_icon = QIcon(logo_path)
        self.setGeometry(600, 250, 700, 700)  #窗口尺寸
        self.setWindowIcon(app_icon)
        
        self.center()  #主界面窗口居中

        #创建菜单栏
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("登录/注册点这里")

        #创建登录按钮
        self.login_action = QAction("登录", self)
        self.login_action.triggered.connect(self.login)
        file_menu.addAction(self.login_action)

        #创建注册按钮
        self.register_action = QAction("注册", self)
        self.register_action.triggered.connect(self.register)
        file_menu.addAction(self.register_action)

        #创建中心部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        #创建添加日记按钮
        self.add_button = QPushButton("添加史记")
        self.add_button.setStyleSheet("QPushButton { "
                                      "  background-color: #CD950C;"  # 设置按钮背景颜色
                                      "  color: white;"  # 设置按钮文字颜色
                                      "  border-style: solid;"  # 设置边框样式
                                      "  border-radius: 5px;"  # 设置边框圆角
                                      "  border-width: 1px;"  # 设置边框宽度
                                      "  padding: 6px;"  # 设置内边距
                                      "  font-size: 16px;"  # 设置字体大小
                                      "  font-weight: bold;"  # 设置字体加粗
                                      "}")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self.add_diary)
        self.layout.addWidget(self.add_button)

        #创建日记列表框
        self.diary_list = QListWidget()
        self.layout.addWidget(self.diary_list)

        #创建显示日记内容的文本框
        self.diary_content = QTextEdit()
        self.diary_content.setReadOnly(True)
        self.layout.addWidget(self.diary_content)

        #创建修改和删除按钮
        self.modify_button = QPushButton("修改史记")
        self.modify_button.setStyleSheet("QPushButton { "
                                         "  background-color: #CD950C;"  # 设置按钮背景颜色
                                         "  color: white;"  # 设置按钮文字颜色
                                         "  border-style: solid;"  # 设置边框样式
                                         "  border-radius: 5px;"  # 设置边框圆角
                                         "  border-width: 1px;"  # 设置边框宽度
                                         "  padding: 6px;"  # 设置内边距
                                         "  font-size: 16px;"  # 设置字体大小
                                         "  font-weight: bold;"  # 设置字体加粗
                                         "}")
        self.modify_button.setEnabled(False)
        self.modify_button.clicked.connect(self.modify_diary)
        self.delete_button = QPushButton("删除史记")
        self.delete_button.setStyleSheet("QPushButton { "
                                         "  background-color: #CD950C;"  # 设置按钮背景颜色
                                         "  color: white;"  # 设置按钮文字颜色
                                         "  border-style: solid;"  # 设置边框样式
                                         "  border-radius: 5px;"  # 设置边框圆角
                                         "  border-width: 1px;"  # 设置边框宽度
                                         "  padding: 6px;"  # 设置内边距
                                         "  font-size: 16px;"  # 设置字体大小
                                         "  font-weight: bold;"  # 设置字体加粗
                                         "}")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete_diary)
        self.layout.addWidget(self.modify_button)
        self.layout.addWidget(self.delete_button)

        self.central_widget.setLayout(self.layout)

        #初始化注册和登录对话框
        self.register_dialog = QDialog(self)
        self.register_dialog.setWindowTitle("注册")
        self.init_register_dialog()

        self.login_dialog = QDialog(self)
        self.login_dialog.setWindowTitle("登录")
        self.init_login_dialog()

        #添加日期选择组件
        self.date_edit = QDateEdit()
        self.layout.addWidget(self.date_edit)

        #显示日记的总数
        self.diary_count_label = QLabel("史记总数: 0")
        self.layout.addWidget(self.diary_count_label)
        
    #将窗口居中显示
    def center(self):
        screen = QApplication.desktop().screen()
        size = self.size()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    #数据库连接
    def create_connection(self):
        return sqlite3.connect("diary.db")

    #确保用户表存在的数据库表创建方法，算异常处理
    def create_user_table(self):
        cursor = self.db_connection.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            password TEXT)""")
        self.db_connection.commit()

    #设置注册对话框布局和组件
    def init_register_dialog(self):
        layout = QVBoxLayout()
        username_label = QLabel("用户名:")
        username_edit = QLineEdit()
        username_edit.setObjectName("username_edit")
        password_label = QLabel("密码:")
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.setObjectName("password_edit")
        register_button = QPushButton("注册")
        register_button.clicked.connect(self.register_user)

        layout.addWidget(username_label)
        layout.addWidget(username_edit)
        layout.addWidget(password_label)
        layout.addWidget(password_edit)
        layout.addWidget(register_button)

        self.register_dialog.setLayout(layout)

    #设置登录对话框布局和组件
    def init_login_dialog(self):
        layout = QVBoxLayout()
        username_label = QLabel("用户名:")
        username_edit = QLineEdit()
        username_edit.setObjectName("username_edit")
        password_label = QLabel("密码:")
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.setObjectName("password_edit")
        login_button = QPushButton("登录")
        login_button.clicked.connect(self.login_user)

        layout.addWidget(username_label)
        layout.addWidget(username_edit)
        layout.addWidget(password_label)
        layout.addWidget(password_edit)
        layout.addWidget(login_button)

        self.login_dialog.setLayout(layout)

    #显示注册对话框
    def register(self):
        self.register_dialog.exec_()

    #设置账号密码，注册要求
    def register_user(self):
        self.register_dialog.exec_()
        username = self.register_dialog.findChild(QLineEdit, "username_edit").text()
        password = self.register_dialog.findChild(QLineEdit, "password_edit").text()

        password_regex = r'^(?=.*[0-9])(?=.*[a-zA-Z])(?=.*[_]).{6,}$'  #正则表达式，密码至少6位数字、下划线和字母的组合

        if not re.match(password_regex, password):
            QMessageBox.warning(self, "注册失败", "密码必须是 6 位及以上数字、下划线和字母的组合。")
            return  #如果密码不符合要求，返回并提示用户

        if username and password:
            self.insert_user(username, self.hash_password(password))
            
    #将新用户信息插入到数据库
    def insert_user(self, username, hashed_password):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, hashed_password))
            self.db_connection.commit()
        except sqlite3.IntegrityError as e:
            QMessageBox.warning(self, "注册失败", "用户名已存在，请选择其他用户名。")

    #显示登录对话框
    def login(self):
        self.login_dialog.exec_()

    #输入账号密码
    def login_user(self):
        self.login_dialog.exec_()
        username = self.login_dialog.findChild(QLineEdit, "username_edit").text()
        password = self.login_dialog.findChild(QLineEdit, "password_edit").text()
        user = self.authenticate_user(username, self.hash_password(password))

        if user:
            self.user_logged_in = True
            self.current_user_id = user[0]
            self.modify_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.add_button.setEnabled(True)
            QMessageBox.information(self, "登录成功", "欢迎回来，" + username)
            self.load_diaries()  #传递当前用户的 ID 给 load_diaries
        else:
            QMessageBox.warning(self, "登录失败", "用户名或密码错误")

    #密码hash加密
    def hash_password(self, password):
        return hashlib.md5(password.encode()).hexdigest()
    
    #验证用户登录信息，找出数据库中用户名和密码都匹配的用户
    def authenticate_user(self, username, hashed_password):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username =? AND password =?", (username, hashed_password))
        user = cursor.fetchone()
        return user

    #创建日记数据库
    def create_diaries_table(self):
        cursor = self.db_connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS diaries")
        cursor.execute("""CREATE TABLE IF NOT EXISTS diaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER, 
                        tag TEXT,
                        title TEXT,
                        date TEXT,
                        content TEXT,
                        modified_date TEXT, 
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        )""")
        self.db_connection.commit()

    #添加新日记
    def add_diary(self):
        #弹出输入框获取日记信息，并关联到当前用户
        tag, ok = QInputDialog.getText(self, "添加史记", "请输入标签:")
        title, ok = QInputDialog.getText(self, "添加史记", "请输入标题:")
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")  # 获取用户选择的日期
        content, ok = QInputDialog.getMultiLineText(self, "添加史记", "请输入内容:")

        if ok:  #将日记信息存入数据库
            cursor = self.db_connection.cursor()
            cursor.execute("INSERT INTO diaries (user_id, tag, title, date, content) VALUES (?,?,?,?,?)",
                           (self.current_user_id, tag, title, selected_date, content))
            self.db_connection.commit()

            #更新日记列表
            self.load_diaries()

    #加载用户日记，根据当前登录用户的ID从数据库中检索日记，并在列表中显示
    def load_diaries(self):
        if self.user_logged_in:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT * FROM diaries WHERE user_id=?", (self.current_user_id,))
            diaries = cursor.fetchall()
            if not diaries:  #如果没有日记，显示提示信息
                QMessageBox.information(self, "提示", "当前用户没有史记。")
                return
            
            self.diary_list.clear()
            #恢复修改状态和日期显示
            for diary in diaries:
                item = QListWidgetItem(f"{diary[2]} - {diary[3]} - {diary[4]}")  #显示标题、日期
                item.setData(Qt.UserRole, diary[0])  #日记的ID
                self.diary_list.addItem(item)
        else:
            QMessageBox.warning(self, "提示", "请先登录。")

        diary_count = len(diaries)  #获取日记的总数
        self.diary_count_label.setText(f"史记总数: {diary_count}")  #更新日记总数标签

        #连接信号，以便在点击列表项时显示日记内容
        self.diary_list.itemClicked.connect(self.view_diary)

    #查看选中日记
    def view_diary(self, item):
        if item:
            #获取日记 ID
            diary_id = item.data(Qt.UserRole)
            #从数据库中查询日记内容
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT tag, title, date, content, modified_date FROM diaries WHERE id=?", (diary_id,))
            diary = cursor.fetchone()  #显示日记信息
            if diary is None:  #检查 diary 是否为 None
                QMessageBox.warning(self, "错误", "无法找到对应的史记。")
                return
            word_count = len(diary[3])
            self.diary_content.setText(
                f"标签: {diary[0]}\n标题: {diary[1]}\n日期: {diary[2]}\n修改日期: {diary[4]}\n字数: {word_count}\n内容: {diary[3]}")

    #修改日记
    def modify_diary(self):
        selected_item = self.diary_list.currentItem()
        if not selected_item:
            return  #如果没有选中项，直接返回

        diary_id = selected_item.data(Qt.UserRole)
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT tag, title, content FROM diaries WHERE id=?", (diary_id,))
        diary = cursor.fetchone()  #获取日记信息
        if not diary:
            QMessageBox.warning(self, "错误", "无法找到史记。")
            return  #如果没有找到日记，就退出函数

        #原始的日记内容
        original_tag, original_title, original_content = diary

        #弹出输入框获取修改后的日记信息
        new_tag, ok = QInputDialog.getText(self, "修改标签", "请输入新标签:", text=original_tag)
        if not ok:
            return  #如果用户取消或未输入新标签，就退出函数

        new_title, ok = QInputDialog.getText(self, "修改标题", "请输入新标题:", text=original_title)
        if not ok:
            return  #如果用户取消或未输入新标题，就退出函数

        #弹出输入框获取新内容，并将新内容追加到原始内容的末尾
        new_content, ok = QInputDialog.getMultiLineText(self, "修改内容", "请输入新内容（保留原始内容）:", text=original_content)
        if not ok:
            return  #如果用户取消或未输入新内容，就退出函数

        #更新日记内容，添加新内容到原始内容之后
        updated_content = new_content

        #更新数据库中的日记信息，并记录修改日期
        current_date = QDate.currentDate().toString("yyyy-MM-dd")  #更新的是实时日期
        cursor.execute("UPDATE diaries SET tag =?, title =?, content =?, modified_date =? WHERE id =?",
                       (new_tag, new_title, updated_content, current_date, diary_id))
        self.db_connection.commit()

        #刷新日记列表和显示内容
        self.load_diaries()

    #删除日记
    def delete_diary(self):
        selected_item = self.diary_list.currentItem()
        if selected_item:
            #弹出确认框
            reply = QMessageBox.question(self, '删除史记',
                                         "您确定要删除选中的史记吗？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:  #获取日记 ID
                diary_id = selected_item.data(Qt.UserRole)
                #从数据库中删除日记
                cursor = self.db_connection.cursor()
                cursor.execute("DELETE FROM diaries WHERE id=?", (diary_id,))
                self.db_connection.commit()
                self.diary_list.takeItem(self.diary_list.row(selected_item))
                self.load_diaries()  #选中项被删除后，更新界面


#程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(logo_path))
    
    splash = SplashScreen()#创建启动画面
    splash.show()  #显示启动画面
    app.processEvents()#等待启动画面关闭

    window = DiaryApp()
    window.create_user_table()  #确保用户表存在
    window.show()
    app.exec_()
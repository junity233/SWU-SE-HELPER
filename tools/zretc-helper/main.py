import requests
from typing import Optional

from PySide6.QtCore import Qt, QDateTime, QSettings
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateTimeEdit,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFrame,
)


class ZretcQuestion:
    question_id : str
    content : str
    score : int

    def __init__(self, question_id: str, content: str, score: int):
        self.question_id = question_id
        self.content = content
        self.score = score

class ZretcHomeworkDetail:
    homework_id : str
    group_id : str
    questions : list[ZretcQuestion]

    def __init__(self, homework_id: str, group_id: str, questions: list[ZretcQuestion]):
        self.homework_id = homework_id
        self.group_id = group_id
        self.questions = questions

class ZretcHomeworkOverview:
    homework_id : str
    title : str
    status : str

    def __init__(self, homework_id: str, title: str, status: str):
        self.homework_id = homework_id
        self.title = title
        self.status = status

class ZretcHomeworkAnswer:
    question_id : str
    subjective_answer : str

    def __init__(self, question_id: str, subjective_answer: str):
        self.question_id = question_id
        self.subjective_answer = subjective_answer

class ZretcClient:
    token : str
    cookie : str
    user_agent : str

    BASE_URL = "https://swu.zretc.net"

    def __init__(self, token: str, cookie: str, user_agent: str):
        self.token = token
        self.cookie = cookie
        self.user_agent = user_agent

    def get(self, url: str, params: dict = {}) -> Optional[dict]:
        headers = {
            "Cookie": self.cookie,
            "User-Agent": self.user_agent,
            "Zretc-Token": self.token,
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6,eu;q=0.5,ja;q=0.4",
            "async": "true",
            "Content-Type": "application/json",
        }

        full_url = self.BASE_URL + url
        print("=== ZretcClient GET ===")
        print("URL:", full_url)
        print("Params:", params)

        res = requests.get(full_url, params=params, headers=headers)
        print("Status code:", res.status_code)

        try:
            res_json = res.json()
        except ValueError:
            print("Response is not valid JSON, raw text:")
            print(res.text)
            return None

        print("Response JSON:", res_json)

        if res_json.get("code") == "1":
            return res_json.get("data")
        else:
            print(f"Error: Get {url} failed. Error message: {res_json.get('message')}")
            return None

    def post(self, url: str, data: dict = {}) -> Optional[dict]:
        headers = {
            "Cookie": self.cookie,
            "User-Agent": self.user_agent,
            "Zretc-Token": self.token,
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6,eu;q=0.5,ja;q=0.4",
            "async": "true",
            "Content-Type": "application/json",
        }

        full_url = self.BASE_URL + url
        print("=== ZretcClient POST ===")
        print("URL:", full_url)
        print("Data:", data)

        res = requests.post(full_url, json=data, headers=headers)
        print("Status code:", res.status_code)

        try:
            res_json = res.json()
        except ValueError:
            print("Response is not valid JSON, raw text:")
            print(res.text)
            return None

        print("Response JSON:", res_json)

        if res_json.get("code") == "1":
            return res_json.get("data")
        else:
            print(f"Error: Get {url} failed. Error message: {res_json.get('message')}")
            print(data)
            return None
    @staticmethod
    def _status_to_str(status: str):
        if status == 0:
            return "未提交"
        elif status == 1:
            return "已提交"
        elif status == 2:
            return "错过"
        else:
            return "Unknown:" + str(status)

    def get_homeworks_list(self,instance_id: str):
        return [ZretcHomeworkOverview(
            homework_id = hw['resCourseware']['homeworkId'],
            title = hw['resCourseware']['name'],
            status = ZretcClient._status_to_str(hw['resCourseware']['status'])
        ) for hw in self.get(f"/api/instances/instances/{instance_id}/stu/homework-list")]

    def get_homework_detail(self,homework_id: str):
        res = self.get(f"/api/homework/homeworks/{homework_id}/questions",{
            "startOrContinue" : "0"
        })

        if res is None:
            return None

        return ZretcHomeworkDetail(
            homework_id=homework_id,
            group_id=res["hwGroupId"],
            questions=[
                ZretcQuestion(
                    question_id=question["queId"],
                    content=question["content"],
                    score=question["score"]
                )
                for question in res["contentQuestions"]
            ]
        )

    def submit_homework(self, homework_id: str, group_id: str, start_time: int, answers: list[ZretcHomeworkAnswer]) -> bool:
        return self.post(
            "/api/homework/submits?submitType=1",
            data={
                "homeworkId": homework_id,
                "hwGroupId": group_id,
                "startTime": start_time,
                "submitAnswers": [
                    {
                        "id": None,
                        "queId": answer.question_id,
                        "queType": 5,
                        "appendix": None,
                        "objectiveSeq": None,
                        "subjectiveAnswer": answer.subjective_answer,
                        "stuQueSeq": 1
                    }
                    for answer in answers
                ]
            }
        )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Zretc Homework Helper")

        self.client = ZretcClient(token="", cookie="", user_agent="")
        self.instance_id: str = ""
        self.current_homework: ZretcHomeworkDetail | None = None
        self.answer_inputs: dict[str, QTextEdit] = {}
        self.settings = QSettings("zretc-helper", "desktop")

        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self._apply_style()

        header = QLabel("Zretc 作业助手")
        header.setStyleSheet("font-size: 22px; font-weight: 700; color: #2a2f45;")
        layout.addWidget(header)

        # Top inputs (two-column grid to use horizontal space)
        top_card = QWidget()
        top_card.setObjectName("card")
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(8)

        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(12)
        top_grid.setVerticalSpacing(8)
        top_grid.setColumnStretch(1, 1)
        top_grid.setColumnStretch(3, 1)
        self.cookie_edit = QLineEdit()
        self.user_agent_edit = QLineEdit()
        self.token_edit = QLineEdit()
        self.instance_edit = QLineEdit()

        self.start_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.start_time_edit.setCalendarPopup(True)

        # Row 0
        top_grid.addWidget(QLabel("Cookie"), 0, 0, alignment=Qt.AlignRight)
        top_grid.addWidget(self.cookie_edit, 0, 1)
        top_grid.addWidget(QLabel("User-Agent"), 0, 2, alignment=Qt.AlignRight)
        top_grid.addWidget(self.user_agent_edit, 0, 3)

        # Row 1
        top_grid.addWidget(QLabel("Zretc-Token"), 1, 0, alignment=Qt.AlignRight)
        top_grid.addWidget(self.token_edit, 1, 1)
        top_grid.addWidget(QLabel("instance_id"), 1, 2, alignment=Qt.AlignRight)
        top_grid.addWidget(self.instance_edit, 1, 3)

        # Row 2
        top_grid.addWidget(QLabel("start time"), 2, 0, alignment=Qt.AlignRight)
        top_grid.addWidget(self.start_time_edit, 2, 1, 1, 3)

        self.fetch_button = QPushButton("获取作业")
        self.fetch_button.clicked.connect(self.on_fetch_homeworks)

        fetch_row = QHBoxLayout()
        fetch_row.addStretch()
        fetch_row.addWidget(self.fetch_button)
        top_grid.addLayout(fetch_row, 3, 0, 1, 4)

        top_layout.addLayout(top_grid)
        layout.addWidget(top_card)

        # Homework selector
        selector_card = QWidget()
        selector_card.setObjectName("card")
        selector_layout = QHBoxLayout(selector_card)
        selector_layout.setContentsMargins(14, 10, 14, 10)
        selector_layout.setSpacing(10)
        selector_layout.addWidget(QLabel("选择作业"))
        self.homework_selector = QComboBox()
        self.homework_selector.currentIndexChanged.connect(self.on_homework_selected)
        selector_layout.addWidget(self.homework_selector, stretch=1)
        selector_layout.addStretch()
        layout.addWidget(selector_card)

        # Questions area inside a scroll view
        self.questions_container = QWidget()
        self.questions_layout = QVBoxLayout(self.questions_container)
        self.questions_layout.setAlignment(Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.questions_container)
        scroll.setObjectName("scrollArea")
        layout.addWidget(scroll, stretch=1)

        # Submit button
        self.submit_button = QPushButton("提交作业")
        self.submit_button.clicked.connect(self.on_submit_homework)
        layout.addWidget(self.submit_button, alignment=Qt.AlignRight)

        self.setCentralWidget(container)

    def _apply_style(self) -> None:
        # Gentle light palette and cards for readability
        self.setStyleSheet(
            """
            QMainWindow { background-color: #f5f7fb; }
            QWidget#card {
                background: #ffffff;
                border: 1px solid #e4e7ed;
                border-radius: 10px;
            }
            QLabel { color: #2f3640; font-size: 14px; }
            QLineEdit, QDateTimeEdit, QComboBox, QTextEdit {
                border: 1px solid #ccd1d9;
                border-radius: 8px;
                padding: 4px 8px;
                background: #fff;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QPushButton {
                background-color: #2d8cf0;
                color: #fff;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1f7bd8; }
            QPushButton:pressed { background-color: #1a68b6; }
            QScrollArea {
                border: none;
            }
            QTextBrowser {
                border: 1px solid #e1e6ed;
                border-radius: 8px;
                background: #fbfcff;
                padding: 8px;
                font-size: 14px;
            }
            """
        )

    def _load_settings(self) -> None:
        self.cookie_edit.setText(self.settings.value("cookie", "", type=str))
        self.user_agent_edit.setText(self.settings.value("userAgent", "", type=str))
        self.token_edit.setText(self.settings.value("token", "", type=str))
        self.instance_edit.setText(self.settings.value("instanceId", "", type=str))
        start_ms = self.settings.value("startTimeMs", None)
        if start_ms is not None:
            try:
                dt = QDateTime.fromMSecsSinceEpoch(int(start_ms))
                if dt.isValid():
                    self.start_time_edit.setDateTime(dt)
            except Exception:
                pass

    def _save_settings(self) -> None:
        self.settings.setValue("cookie", self.cookie_edit.text())
        self.settings.setValue("userAgent", self.user_agent_edit.text())
        self.settings.setValue("token", self.token_edit.text())
        self.settings.setValue("instanceId", self.instance_edit.text())
        self.settings.setValue("startTimeMs", int(self.start_time_edit.dateTime().toMSecsSinceEpoch()))

    def on_fetch_homeworks(self) -> None:
        cookie = self.cookie_edit.text().strip()
        user_agent = self.user_agent_edit.text().strip()
        token = self.token_edit.text().strip()
        instance_id = self.instance_edit.text().strip()

        if not all([cookie, user_agent, token, instance_id]):
            QMessageBox.warning(self, "缺少参数", "请填写 Cookie、User-Agent、Zretc-Token 和 instance_id。")
            return

        # Update client settings
        self.client.cookie = cookie
        self.client.user_agent = user_agent
        self.client.token = token
        self.instance_id = instance_id
        self._save_settings()

        try:
            homeworks = self.client.get_homeworks_list(instance_id)
        except Exception as exc:  # Network errors bubble up here
            QMessageBox.critical(self, "请求失败", f"获取作业列表失败：{exc}")
            return

        if not homeworks:
            QMessageBox.information(self, "无作业", "未获取到作业列表。")
            self.homework_selector.clear()
            self.clear_questions()
            return

        self.homework_selector.blockSignals(True)
        self.homework_selector.clear()
        for hw in homeworks:
            display = f"{hw.title} ({hw.status})"
            self.homework_selector.addItem(display, hw)
        self.homework_selector.blockSignals(False)

        # Auto load first homework if present
        if self.homework_selector.count() > 0:
            self.homework_selector.setCurrentIndex(0)
            self.on_homework_selected(0)

    def on_homework_selected(self, index: int) -> None:
        homework: ZretcHomeworkOverview | None = self.homework_selector.currentData()
        if homework is None:
            self.clear_questions()
            return

        try:
            detail = self.client.get_homework_detail(homework.homework_id)
        except Exception as exc:
            QMessageBox.critical(self, "请求失败", f"获取作业详情失败：{exc}")
            return

        if detail is None:
            QMessageBox.warning(self, "作业加载失败", "未能加载该作业的详情。")
            self.clear_questions()
            return

        self.current_homework = detail
        self.render_questions(detail)

    def clear_questions(self, preserve_homework: bool = False) -> None:
        if not preserve_homework:
            self.current_homework = None
        self.answer_inputs = {}
        while self.questions_layout.count():
            item = self.questions_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def copy_question_content(self, view: QTextBrowser) -> None:
        text = view.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "复制失败", "题目内容为空，无法复制。")
            return
        QApplication.clipboard().setText(text)

    def render_questions(self, detail: ZretcHomeworkDetail) -> None:
        self.clear_questions(preserve_homework=True)

        for idx, question in enumerate(detail.questions, start=1):
            wrapper = QWidget()
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(12, 10, 12, 12)
            wrapper_layout.setSpacing(8)
            wrapper.setObjectName("card")

            title = QLabel(f"题目 {idx} (ID: {question.question_id}, 分值: {question.score})")
            title.setStyleSheet("font-weight: bold;")
            wrapper_layout.addWidget(title)

            content_view = QTextBrowser()
            content_view.setHtml(question.content)
            content_view.setMinimumHeight(120)
            wrapper_layout.addWidget(content_view)

            button_row = QHBoxLayout()
            button_row.addStretch()
            copy_btn = QPushButton("复制题目")
            copy_btn.setFixedWidth(90)
            copy_btn.clicked.connect(lambda _, view=content_view: self.copy_question_content(view))
            button_row.addWidget(copy_btn)
            wrapper_layout.addLayout(button_row)

            answer_edit = QTextEdit()
            answer_edit.setPlaceholderText("在此输入答案，将提交到 subjectiveAnswer")
            answer_edit.setMinimumHeight(100)
            wrapper_layout.addWidget(answer_edit)

            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setStyleSheet("color: #e4e7ed;")

            self.questions_layout.addWidget(wrapper)
            self.questions_layout.addWidget(separator)

            self.answer_inputs[question.question_id] = answer_edit

        self.questions_layout.addStretch()

    def on_submit_homework(self) -> None:
        if not self.current_homework:
            QMessageBox.warning(self, "未选择作业", "请先选择并加载一个作业。")
            return

        start_dt = self.start_time_edit.dateTime()
        start_time_ms = int(start_dt.toMSecsSinceEpoch())

        for q in self.current_homework.questions:
            if not self.answer_inputs[q.question_id].toPlainText():
                QMessageBox.warning(self, "未填写答案", f"请填写题目 {q.question_id} 的答案。")
                return

        answers = [
            ZretcHomeworkAnswer(question_id=q.question_id, subjective_answer=self.answer_inputs[q.question_id].toPlainText())
            for q in self.current_homework.questions
        ]

        try:
            result = self.client.submit_homework(
                homework_id=self.current_homework.homework_id,
                group_id=self.current_homework.group_id,
                start_time=start_time_ms,
                answers=answers,
            )
        except Exception as exc:
            QMessageBox.critical(self, "提交失败", f"提交作业时出现错误：{exc}")
            return

        if result:
            QMessageBox.information(self, "提交成功", "作业已提交。")
        else:
            QMessageBox.warning(self, "提交完成", f"提交已发送，返回结果：{result}")

    def closeEvent(self, event) -> None:
        self._save_settings()
        super().closeEvent(event)


def main() -> None:
    app = QApplication([])
    window = MainWindow()
    window.resize(900, 700)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()

import customtkinter as ctk

class CustomTkinterCop:
    SUPPORTED_LANGUAGES = ["Python","TypeScript","C","C++","C#","HTML","CSS","JS","Go","Rust","md","json"]
    def __init__(self, root, language="Python", codecompleter=True):
        self.root = root
        self.language = language
        self.codecompleter = codecompleter
        self.create_entry()

    def create_entry(self):
        self.text = ctk.CTkTextbox(self.root, height=400, width=800)
        self.text.pack()
        if self.codecompleter:
            self.text.bind("<KeyRelease>", self.auto_complete)

    def auto_complete(self, event=None):
        current = self.text.get("1.0", "end")
        suggestion = f"Suggestion ({self.language}): print() example"
        try:
            self.suggestion_label.destroy()
        except:
            pass
        self.suggestion_label = ctk.CTkLabel(self.root, text=suggestion, text_color="gray")
        self.suggestion_label.place(relx=0.75, rely=0.9)

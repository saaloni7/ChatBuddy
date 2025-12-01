import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, Menu, Toplevel, Scale
import time
import threading
import random
import json
import os
from datetime import datetime
import pickle
from collections import deque

# -------------------- Additional Libraries -------------------- #
# Run these commands in terminal to install required packages:
# pip install textblob plyer

try:
    from textblob import TextBlob
    SENTIMENT_ANALYSIS = True
except ImportError:
    SENTIMENT_ANALYSIS = False
    
try:
    from plyer import notification
    NOTIFICATIONS = True
except ImportError:
    NOTIFICATIONS = False

# -------------------- Configuration -------------------- #
class Config:
    THEMES = {
        "Light": {
            "bg": "#FFFFFF",
            "fg": "#000000",
            "user_bg": "#0078D4",
            "user_fg": "#FFFFFF",
            "bot_bg": "#F0F0F0",
            "bot_fg": "#000000",
            "input_bg": "#FFFFFF",
            "input_fg": "#000000"
        },
        "Dark": {
            "bg": "#2D2D30",
            "fg": "#FFFFFF",
            "user_bg": "#0E639C",
            "user_fg": "#FFFFFF",
            "bot_bg": "#3E3E42",
            "bot_fg": "#FFFFFF",
            "input_bg": "#3E3E42",
            "input_fg": "#FFFFFF"
        },
        "Blue": {
            "bg": "#E3F2FD",
            "fg": "#0D47A1",
            "user_bg": "#1976D2",
            "user_fg": "#FFFFFF",
            "bot_bg": "#BBDEFB",
            "bot_fg": "#0D47A1",
            "input_bg": "#FFFFFF",
            "input_fg": "#000000"
        }
    }
    
    def __init__(self):
        self.theme = "Light"
        self.font_size = 10
        self.enable_notifications = True
        self.save_history = True
        self.max_memory = 10
        self.auto_save = True

# -------------------- Chat History Manager -------------------- #
class ChatHistory:
    def __init__(self):
        self.history_file = "chat_history.json"
        self.conversations = self.load_history()
        
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_conversation(self, messages, session_id):
        conversation = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": messages
        }
        self.conversations.append(conversation)
        
        # Keep only last 50 conversations
        if len(self.conversations) > 50:
            self.conversations = self.conversations[-50:]
            
        self.save_to_file()
    
    def save_to_file(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.conversations, f, indent=2)
        except:
            pass
    
    def export_conversation(self, session_id, filename):
        for conv in self.conversations:
            if conv["session_id"] == session_id:
                with open(filename, 'w') as f:
                    json.dump(conv, f, indent=2)
                return True
        return False

# -------------------- Conversation Memory -------------------- #
class ConversationMemory:
    def __init__(self, max_memory=10):
        self.memory = deque(maxlen=max_memory)
        self.user_name = None
        self.user_mood = "neutral"
        
    def add_exchange(self, user_msg, bot_response):
        self.memory.append({
            "user": user_msg,
            "bot": bot_response,
            "timestamp": time.time(),
            "time": datetime.now().strftime("%H:%M:%S")
        })
    
    def get_context(self, n=3):
        return list(self.memory)[-n:] if len(self.memory) >= n else list(self.memory)
    
    def clear(self):
        self.memory.clear()
    
    def get_conversation_summary(self):
        if not self.memory:
            return "No conversation yet"
        
        topics = set()
        for exchange in self.memory:
            msg = exchange["user"].lower()
            if any(word in msg for word in ["hello", "hi", "hey"]):
                topics.add("greeting")
            if any(word in msg for word in ["how are", "how do you"]):
                topics.add("mood inquiry")
            if any(word in msg for word in ["joke", "funny"]):
                topics.add("humor")
            if any(word in msg for word in ["bye", "goodbye"]):
                topics.add("farewell")
        
        return f"Topics discussed: {', '.join(topics) if topics else 'Various'}"

# -------------------- Session Manager -------------------- #
class SessionManager:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now()
        self.message_count = 0
        self.user_messages = 0
        self.bot_messages = 0
        
    def get_stats(self):
        duration = datetime.now() - self.start_time
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "session_id": self.session_id,
            "duration": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "total_messages": self.message_count,
            "user_messages": self.user_messages,
            "bot_messages": self.bot_messages,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "avg_response_time": "0.5s"  # Could be calculated
        }

# -------------------- Enhanced Response Engine -------------------- #
class ResponseEngine:
    def __init__(self):
        self.responses = self.load_responses()
        self.fallback_responses = [
            "That's interesting! Tell me more about it.",
            "I'm not sure I understand. Could you rephrase that?",
            "I'm still learning about that topic. What else would you like to chat about?",
            "Thanks for sharing! How's your day going?"
        ]
        
    def load_responses(self):
        responses = {
            "greetings": {
                "patterns": ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"],
                "responses": [
                    "Hello! 😊 How can I assist you today?",
                    "Hi there! 👋 Nice to see you!",
                    "Hey! How's your day going?"
                ]
            },
            "farewell": {
                "patterns": ["bye", "goodbye", "see you", "take care"],
                "responses": [
                    "Goodbye! 👋 Have a wonderful day!",
                    "See you soon! 😊",
                    "Take care! Looking forward to our next chat!"
                ]
            },
            "gratitude": {
                "patterns": ["thanks", "thank you", "appreciate"],
                "responses": [
                    "You're welcome! 😇",
                    "My pleasure! 😊",
                    "Anytime! Happy to help!"
                ]
            },
            "identity": {
                "patterns": ["who are you", "what is your name", "what are you"],
                "responses": [
                    "I'm ChatBuddy Pro, your AI assistant! 🤖",
                    "I'm your friendly chatbot, here to help and chat! 😄"
                ]
            },
            "mood": {
                "patterns": ["how are you", "how do you feel", "how's it going"],
                "responses": [
                    "I'm doing great, thanks for asking! Ready to help! 😊",
                    "All systems go! How about you?",
                    "Feeling fantastic! What's on your mind?"
                ]
            },
            "joke": {
                "patterns": ["joke", "funny", "make me laugh"],
                "responses": [
                    "Why don't scientists trust atoms? Because they make up everything! 😂",
                    "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
                    "What do you call a fake noodle? An impasta! 🍝"
                ]
            },
            "help": {
                "patterns": ["help", "what can you do", "features"],
                "responses": [
                    "I can chat with you, tell jokes, analyze sentiment, remember our conversation, and much more! Try saying 'tell me a joke' or 'analyze my mood'! 🎯",
                    "I'm here to chat, help, and entertain! You can ask me about anything, or try our special features like file attachments or sentiment analysis! ✨"
                ]
            },
            "time": {
                "patterns": ["time", "what time", "current time"],
                "responses": [
                    f"The current time is {datetime.now().strftime('%H:%M:%S')} ⏰",
                    f"According to my clock, it's {datetime.now().strftime('%I:%M %p')} 🕐"
                ]
            }
        }
        return responses
    
    def get_response(self, user_msg, context=None, sentiment=None):
        user_msg_lower = user_msg.lower()
        
        # Check for exact matches first
        for category, data in self.responses.items():
            for pattern in data["patterns"]:
                if pattern in user_msg_lower:
                    response = random.choice(data["responses"])
                    
                    # Add context awareness
                    if context and len(context) > 0:
                        last_topic = context[-1].get("user", "").lower()
                        if "how are" in last_topic and "fine" in user_msg_lower:
                            response = "Glad to hear you're doing well! 😊 " + response
                    
                    # Adjust based on sentiment
                    if sentiment:
                        if sentiment == "positive":
                            response = "That's wonderful! 😊 " + response
                        elif sentiment == "negative":
                            response = "I'm here for you. ❤️ " + response
                    
                    return response
        
        # If no match, use contextual or fallback response
        if context and len(context) > 0:
            last_exchange = context[-1]
            last_bot_msg = last_exchange.get("bot", "").lower()
            
            if "how are" in last_bot_msg:
                if any(word in user_msg_lower for word in ["good", "great", "fine", "well"]):
                    return "I'm glad to hear that! 😊 What would you like to talk about?"
                elif any(word in user_msg_lower for word in ["bad", "sad", "not good", "tired"]):
                    return "I'm sorry to hear that. I'm here to chat if you want to talk about it. ❤️"
        
        return random.choice(self.fallback_responses)
    
    def analyze_sentiment(self, text):
        if SENTIMENT_ANALYSIS:
            try:
                analysis = TextBlob(text)
                polarity = analysis.sentiment.polarity
                
                if polarity > 0.3:
                    return "positive", "😊", polarity
                elif polarity < -0.3:
                    return "negative", "😔", polarity
                else:
                    return "neutral", "😐", polarity
            except:
                return "neutral", "😐", 0
        else:
            # Simple keyword-based fallback
            positive_words = ["good", "great", "love", "happy", "excellent", "awesome", "wonderful"]
            negative_words = ["bad", "sad", "hate", "angry", "terrible", "awful", "upset"]
            
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count > neg_count:
                return "positive", "😊", 0.5
            elif neg_count > pos_count:
                return "negative", "😔", -0.5
            else:
                return "neutral", "😐", 0

# -------------------- Main Application -------------------- #
class ChatBuddyPro:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ChatBuddy Pro 🤖")
        self.root.geometry("600x700")
        
        # Initialize components
        self.config = Config()
        self.history = ChatHistory()
        self.memory = ConversationMemory()
        self.session = SessionManager()
        self.engine = ResponseEngine()
        
        # Message storage for current session
        self.current_messages = []
        
        # Typing indicator flag
        self.typing = False
        
        # Setup UI
        self.setup_menu()
        self.setup_ui()
        self.apply_theme()
        
        # Auto-save timer
        if self.config.auto_save:
            self.root.after(30000, self.auto_save)  # Auto-save every 30 seconds
    
    def setup_menu(self):
        menubar = Menu(self.root)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export Chat", command=self.export_chat)
        file_menu.add_command(label="Save Session", command=self.save_session)
        file_menu.add_command(label="Load Session", command=self.load_session)
        file_menu.add_separator()
        file_menu.add_command(label="Clear History", command=self.clear_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Settings", command=self.open_settings)
        edit_menu.add_command(label="Themes", command=self.open_theme_chooser)
        
        # View menu
        view_menu = Menu(menubar, tearoff=0)
        view_menu.add_command(label="Session Stats", command=self.show_stats)
        view_menu.add_command(label="Chat History", command=self.show_history)
        
        # Tools menu
        tools_menu = Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Analyze Sentiment", command=self.analyze_current_sentiment)
        tools_menu.add_command(label="Conversation Summary", command=self.show_summary)
        
        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Help", command=self.show_help)
        
        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        menubar.add_cascade(label="View", menu=view_menu)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat display area with scrollbar
        chat_frame = tk.Frame(main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_area = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Arial", self.config.font_size),
            spacing1=5,
            spacing3=5
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        self.chat_area.config(state='disabled')
        
        # Configure tags for message styling
        self.setup_text_tags()
        
        # Input area
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Attachment button
        self.attach_btn = tk.Button(
            input_frame,
            text="📎",
            command=self.attach_file,
            font=("Arial", 12),
            relief=tk.FLAT,
            bg="#4CAF50",
            fg="white"
        )
        self.attach_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Input field with auto-complete
        self.input_field = tk.Entry(
            input_frame,
            font=("Arial", self.config.font_size),
            relief=tk.SUNKEN,
            bd=2
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.input_field.bind("<Return>", lambda e: self.send_message())
        self.input_field.bind("<KeyRelease>", self.suggest_completion)
        
        # Send button
        self.send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            font=("Arial", 10, "bold"),
            bg="#2196F3",
            fg="white",
            relief=tk.RAISED,
            padx=20
        )
        self.send_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Bottom button panel
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Clear button
        clear_btn = tk.Button(
            button_frame,
            text="Clear Chat",
            command=self.clear_chat,
            bg="#FF5722",
            fg="white"
        )
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Sentiment button
        sentiment_btn = tk.Button(
            button_frame,
            text="Analyze Mood",
            command=self.analyze_sentiment,
            bg="#9C27B0",
            fg="white"
        )
        sentiment_btn.pack(side=tk.LEFT, padx=2)
        
        # Save button
        save_btn = tk.Button(
            button_frame,
            text="Save Chat",
            command=self.save_current_chat,
            bg="#4CAF50",
            fg="white"
        )
        save_btn.pack(side=tk.LEFT, padx=2)
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready | Session started",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Suggestion listbox (hidden by default)
        self.suggestion_listbox = tk.Listbox(main_frame, height=4, font=("Arial", 9))
        self.suggestion_listbox.bind("<<ListboxSelect>>", self.use_suggestion)
        
        # Initial welcome message
        self.add_message("ChatBuddy Pro", "Hello! I'm ChatBuddy Pro, your enhanced AI assistant! 🤖\nType 'help' to see what I can do.", "bot")
    
    def setup_text_tags(self):
        # User message style
        self.chat_area.tag_config("user", 
            background=self.config.THEMES[self.config.theme]["user_bg"],
            foreground=self.config.THEMES[self.config.theme]["user_fg"],
            lmargin1=50,
            rmargin=10,
            spacing2=5,
            relief=tk.RAISED,
            borderwidth=2
        )
        
        # Bot message style
        self.chat_area.tag_config("bot",
            background=self.config.THEMES[self.config.theme]["bot_bg"],
            foreground=self.config.THEMES[self.config.theme]["bot_fg"],
            lmargin1=10,
            rmargin=50,
            spacing2=5,
            relief=tk.SUNKEN,
            borderwidth=1
        )
        
        # Timestamp style
        self.chat_area.tag_config("timestamp",
            foreground="gray",
            font=("Arial", 8)
        )
        
        # System message style
        self.chat_area.tag_config("system",
            foreground="blue",
            font=("Arial", 9, "italic")
        )
        
        # Error message style
        self.chat_area.tag_config("error",
            foreground="red",
            font=("Arial", 9)
        )
        
        # Typing indicator style
        self.chat_area.tag_config("typing",
            foreground="gray",
            font=("Arial", 9, "italic")
        )
    
    def apply_theme(self):
        theme = self.config.THEMES[self.config.theme]
        
        self.root.configure(bg=theme["bg"])
        
        # Update chat area
        self.chat_area.config(
            bg=theme["bg"],
            fg=theme["fg"],
            font=("Arial", self.config.font_size)
        )
        
        # Update input field
        self.input_field.config(
            bg=theme["input_bg"],
            fg=theme["input_fg"],
            insertbackground=theme["fg"]
        )
        
        # Update text tags
        self.setup_text_tags()
        
        # Update status bar
        self.status_bar.config(bg=theme["bg"], fg=theme["fg"])
    
    def add_message(self, sender, message, msg_type="user", show_time=True):
        self.chat_area.config(state='normal')
        
        # Add timestamp
        if show_time:
            timestamp = datetime.now().strftime("%H:%M")
            self.chat_area.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Add sender name
        self.chat_area.insert(tk.END, f"{sender}: ", "bold")
        
        # Add message with appropriate styling
        if msg_type == "user":
            self.chat_area.insert(tk.END, f"{message}\n\n", "user")
        elif msg_type == "bot":
            self.chat_area.insert(tk.END, f"{message}\n\n", "bot")
        elif msg_type == "system":
            self.chat_area.insert(tk.END, f"{message}\n\n", "system")
        elif msg_type == "error":
            self.chat_area.insert(tk.END, f"{message}\n\n", "error")
        
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END)
        
        # Store in current messages
        self.current_messages.append({
            "sender": sender,
            "message": message,
            "type": msg_type,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update status
        self.update_status(f"Message from {sender}")
    
    def send_message(self):
        user_msg = self.input_field.get().strip()
        if not user_msg:
            return
        
        # Clear input field
        self.input_field.delete(0, tk.END)
        self.suggestion_listbox.place_forget()
        
        # Add user message to chat
        self.add_message("You", user_msg, "user")
        self.session.message_count += 1
        self.session.user_messages += 1
        
        # Analyze sentiment
        sentiment, emoji, score = self.engine.analyze_sentiment(user_msg)
        
        # Get response with context
        context = self.memory.get_context()
        response = self.engine.get_response(user_msg, context, sentiment)
        
        # Store in memory
        self.memory.add_exchange(user_msg, response)
        
        # Show typing indicator
        self.show_typing_indicator()
        
        # Bot response with delay
        def bot_reply():
            time.sleep(0.8 + random.random() * 0.5)  # Natural delay
            
            # Hide typing indicator
            self.hide_typing_indicator()
            
            # Add sentiment emoji if not neutral
            if sentiment != "neutral":
                response_with_emoji = f"{emoji} {response}"
            else:
                response_with_emoji = response
            
            self.add_message("ChatBuddy Pro", response_with_emoji, "bot")
            self.session.message_count += 1
            self.session.bot_messages += 1
            
            # Send notification
            if self.config.enable_notifications and NOTIFICATIONS:
                self.send_notification("ChatBuddy Pro", "New message received")
        
        threading.Thread(target=bot_reply, daemon=True).start()
    
    def show_typing_indicator(self):
        if not self.typing:
            self.typing = True
            self.chat_area.config(state='normal')
            self.chat_area.insert(tk.END, "ChatBuddy Pro is typing...\n", "typing")
            self.chat_area.config(state='disabled')
            self.chat_area.see(tk.END)
    
    def hide_typing_indicator(self):
        if self.typing:
            self.typing = False
            self.chat_area.config(state='normal')
            # Remove the last line (typing indicator)
            end_line = self.chat_area.index(tk.END)
            last_line_num = int(end_line.split('.')[0]) - 1
            self.chat_area.delete(f"{last_line_num}.0", tk.END)
            self.chat_area.config(state='disabled')
    
    def suggest_completion(self, event):
        suggestions = [
            "hello", "how are you", "tell me a joke", "what time is it",
            "thank you", "goodbye", "help", "analyze my mood"
        ]
        
        current_text = self.input_field.get().lower()
        
        if not current_text:
            self.suggestion_listbox.place_forget()
            return
        
        matches = [s for s in suggestions if s.startswith(current_text)]
        
        if matches:
            # Position listbox below input field
            x = self.input_field.winfo_rootx() - self.root.winfo_rootx()
            y = self.input_field.winfo_rooty() - self.root.winfo_rooty() + self.input_field.winfo_height()
            
            self.suggestion_listbox.delete(0, tk.END)
            for match in matches[:4]:  # Show max 4 suggestions
                self.suggestion_listbox.insert(tk.END, match)
            
            self.suggestion_listbox.place(x=x, y=y, width=self.input_field.winfo_width())
        else:
            self.suggestion_listbox.place_forget()
    
    def use_suggestion(self, event):
        selection = self.suggestion_listbox.curselection()
        if selection:
            suggestion = self.suggestion_listbox.get(selection[0])
            self.input_field.delete(0, tk.END)
            self.input_field.insert(0, suggestion)
            self.suggestion_listbox.place_forget()
    
    def attach_file(self):
        filepath = filedialog.askopenfilename(
            title="Select a file to attach",
            filetypes=[
                ("All files", "*.*"),
                ("Text files", "*.txt"),
                ("Images", "*.png *.jpg *.jpeg *.gif"),
                ("Documents", "*.pdf *.doc *.docx")
            ]
        )
        
        if filepath:
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath) / 1024  # KB
            
            self.add_message("System", f"📎 Attached: {filename} ({file_size:.1f} KB)", "system")
            
            # Store attachment info
            self.current_messages.append({
                "type": "attachment",
                "filename": filename,
                "path": filepath,
                "size": file_size,
                "timestamp": datetime.now().isoformat()
            })
    
    def analyze_sentiment(self):
        # Analyze the last user message
        if self.current_messages:
            user_messages = [msg for msg in self.current_messages 
                           if msg.get("sender") == "You"]
            
            if user_messages:
                last_msg = user_messages[-1]["message"]
                sentiment, emoji, score = self.engine.analyze_sentiment(last_msg)
                
                self.add_message("System", 
                    f"Sentiment Analysis: {sentiment.capitalize()} {emoji} (Score: {score:.2f})",
                    "system")
                
                # Provide feedback based on sentiment
                feedback = {
                    "positive": "Great to see you're in a positive mood! 😊",
                    "negative": "I'm here if you want to talk. ❤️",
                    "neutral": "Keeping things balanced, I see! 😊"
                }
                
                if sentiment in feedback:
                    self.add_message("ChatBuddy Pro", feedback[sentiment], "bot")
    
    def analyze_current_sentiment(self):
        if self.current_messages:
            all_text = " ".join([msg["message"] for msg in self.current_messages 
                               if msg.get("type") in ["user", "bot"] and msg.get("sender") == "You"])
            
            if all_text:
                sentiment, emoji, score = self.engine.analyze_sentiment(all_text)
                
                messagebox.showinfo("Sentiment Analysis",
                    f"Overall Conversation Sentiment:\n\n"
                    f"Mood: {sentiment.capitalize()} {emoji}\n"
                    f"Score: {score:.2f}\n\n"
                    f"Positive: > 0.3\n"
                    f"Neutral: -0.3 to 0.3\n"
                    f"Negative: < -0.3")
    
    def clear_chat(self):
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear the chat?"):
            self.chat_area.config(state='normal')
            self.chat_area.delete(1.0, tk.END)
            self.chat_area.config(state='disabled')
            
            # Save current conversation before clearing
            if self.current_messages:
                self.history.save_conversation(self.current_messages, self.session.session_id)
            
            self.current_messages.clear()
            self.memory.clear()
            
            self.add_message("System", "Chat cleared. New session started.", "system")
            self.update_status("Chat cleared | New session")
    
    def save_current_chat(self):
        if not self.current_messages:
            messagebox.showwarning("No Messages", "No messages to save.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump({
                        "session_info": self.session.get_stats(),
                        "messages": self.current_messages,
                        "summary": self.memory.get_conversation_summary()
                    }, f, indent=2)
                
                messagebox.showinfo("Success", f"Chat saved to:\n{filename}")
                self.update_status(f"Chat saved to {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save chat: {str(e)}")
    
    def export_chat(self):
        if not self.current_messages:
            messagebox.showwarning("No Messages", "No messages to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("=" * 50 + "\n")
                    f.write(f"CHAT EXPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for msg in self.current_messages:
                        if msg.get("type") == "attachment":
                            f.write(f"[ATTACHMENT] {msg.get('filename')} ({msg.get('size', 0):.1f} KB)\n")
                        else:
                            timestamp = msg.get('timestamp', '')
                            if timestamp:
                                try:
                                    dt = datetime.fromisoformat(timestamp)
                                    timestamp = dt.strftime("%H:%M")
                                except:
                                    pass
                            
                            sender = msg.get('sender', 'System')
                            message = msg.get('message', '')
                            f.write(f"[{timestamp}] {sender}: {message}\n")
                
                messagebox.showinfo("Success", f"Chat exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export chat: {str(e)}")
    
    def save_session(self):
        session_data = {
            "session": self.session.get_stats(),
            "memory": list(self.memory.memory),
            "config": self.config.__dict__,
            "messages": self.current_messages
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".chat",
            filetypes=[("Chat session", "*.chat"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'wb') as f:
                    pickle.dump(session_data, f)
                messagebox.showinfo("Success", "Session saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save session: {str(e)}")
    
    def load_session(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Chat session", "*.chat"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'rb') as f:
                    session_data = pickle.load(f)
                
                # Clear current chat
                self.chat_area.config(state='normal')
                self.chat_area.delete(1.0, tk.END)
                self.chat_area.config(state='disabled')
                
                # Load messages
                self.current_messages = session_data.get("messages", [])
                for msg in self.current_messages:
                    if msg.get("type") == "system":
                        self.add_message("System", msg.get("message", ""), "system", show_time=False)
                    elif msg.get("sender") == "You":
                        self.add_message("You", msg.get("message", ""), "user", show_time=False)
                    elif msg.get("sender") == "ChatBuddy Pro":
                        self.add_message("ChatBuddy Pro", msg.get("message", ""), "bot", show_time=False)
                
                # Load memory
                self.memory.memory = deque(session_data.get("memory", []), maxlen=10)
                
                messagebox.showinfo("Success", "Session loaded successfully!")
                self.update_status(f"Loaded session from {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load session: {str(e)}")
    
    def clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all chat history?"):
            self.history.conversations.clear()
            self.history.save_to_file()
            messagebox.showinfo("Success", "Chat history cleared.")
    
    def show_stats(self):
        stats = self.session.get_stats()
        
        stats_text = f"""Session Statistics:
────────────────
Session ID: {stats['session_id']}
Start Time: {stats['start_time']}
Duration: {stats['duration']}
────────────────
Total Messages: {stats['total_messages']}
- User: {stats['user_messages']}
- Bot: {stats['bot_messages']}
────────────────
Memory Usage: {len(self.memory.memory)} exchanges
Context Window: {self.memory.maxlen}
────────────────"""
        
        messagebox.showinfo("Session Statistics", stats_text)
    
    def show_summary(self):
        summary = self.memory.get_conversation_summary()
        messagebox.showinfo("Conversation Summary", summary)
    
    def show_history(self):
        history_window = Toplevel(self.root)
        history_window.title("Chat History")
        history_window.geometry("500x400")
        
        history_text = scrolledtext.ScrolledText(history_window, wrap=tk.WORD)
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        if self.history.conversations:
            for i, conv in enumerate(self.history.conversations[-10:], 1):  # Show last 10
                timestamp = conv.get("timestamp", "").split("T")[0]
                history_text.insert(tk.END, 
                    f"{i}. Session {conv['session_id']} ({timestamp})\n"
                    f"   Messages: {conv['message_count']}\n"
                    f"   {'-'*40}\n")
        else:
            history_text.insert(tk.END, "No chat history available.")
        
        history_text.config(state='disabled')
    
    def open_settings(self):
        settings_window = Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x500")
        
        # Theme selection
        tk.Label(settings_window, text="Theme:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        theme_var = tk.StringVar(value=self.config.theme)
        theme_menu = tk.OptionMenu(settings_window, theme_var, *self.config.THEMES.keys(),
                                  command=lambda t: self.change_theme(t))
        theme_menu.pack(fill=tk.X, padx=20, pady=5)
        
        # Font size
        tk.Label(settings_window, text="Font Size:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        font_size_var = tk.IntVar(value=self.config.font_size)
        font_scale = Scale(settings_window, from_=8, to=20, orient=tk.HORIZONTAL, 
                          variable=font_size_var, command=lambda s: self.change_font_size(int(s)))
        font_scale.pack(fill=tk.X, padx=20, pady=5)
        
        # Checkboxes
        notifications_var = tk.BooleanVar(value=self.config.enable_notifications)
        notifications_cb = tk.Checkbutton(settings_window, text="Enable Notifications",
                                         variable=notifications_var,
                                         command=lambda: self.toggle_notifications(notifications_var.get()))
        notifications_cb.pack(anchor=tk.W, padx=20, pady=10)
        
        save_history_var = tk.BooleanVar(value=self.config.save_history)
        save_history_cb = tk.Checkbutton(settings_window, text="Save Chat History",
                                        variable=save_history_var,
                                        command=lambda: self.toggle_save_history(save_history_var.get()))
        save_history_cb.pack(anchor=tk.W, padx=20, pady=10)
        
        auto_save_var = tk.BooleanVar(value=self.config.auto_save)
        auto_save_cb = tk.Checkbutton(settings_window, text="Auto-save (every 30s)",
                                     variable=auto_save_var,
                                     command=lambda: self.toggle_auto_save(auto_save_var.get()))
        auto_save_cb.pack(anchor=tk.W, padx=20, pady=10)
        
        # Close button
        tk.Button(settings_window, text="Apply & Close", 
                 command=settings_window.destroy,
                 bg="#4CAF50", fg="white").pack(pady=20)
    
    def open_theme_chooser(self):
        theme_window = Toplevel(self.root)
        theme_window.title("Choose Theme")
        theme_window.geometry("300x200")
        
        for theme_name in self.config.THEMES.keys():
            theme_btn = tk.Button(
                theme_window,
                text=theme_name,
                command=lambda t=theme_name: self.change_theme(t),
                bg=self.config.THEMES[theme_name]["user_bg"],
                fg=self.config.THEMES[theme_name]["user_fg"],
                font=("Arial", 10, "bold"),
                padx=20,
                pady=10
            )
            theme_btn.pack(fill=tk.X, padx=20, pady=5)
    
    def change_theme(self, theme_name):
        self.config.theme = theme_name
        self.apply_theme()
        self.update_status(f"Theme changed to {theme_name}")
    
    def change_font_size(self, size):
        self.config.font_size = size
        self.chat_area.config(font=("Arial", size))
        self.input_field.config(font=("Arial", size))
    
    def toggle_notifications(self, enabled):
        self.config.enable_notifications = enabled
        status = "enabled" if enabled else "disabled"
        self.update_status(f"Notifications {status}")
    
    def toggle_save_history(self, enabled):
        self.config.save_history = enabled
        status = "enabled" if enabled else "disabled"
        self.update_status(f"History saving {status}")
    
    def toggle_auto_save(self, enabled):
        self.config.auto_save = enabled
        status = "enabled" if enabled else "disabled"
        self.update_status(f"Auto-save {status}")
        
        if enabled:
            self.root.after(30000, self.auto_save)
    
    def auto_save(self):
        if self.config.auto_save and self.current_messages:
            self.history.save_conversation(self.current_messages, self.session.session_id)
            self.update_status("Auto-saved conversation")
        
        # Schedule next auto-save
        if self.config.auto_save:
            self.root.after(30000, self.auto_save)
    
    def send_notification(self, title, message):
        if self.config.enable_notifications and NOTIFICATIONS:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    timeout=3
                )
            except:
                pass  # Silent fail if notifications not supported
    
    def update_status(self, message):
        stats = self.session.get_stats()
        self.status_bar.config(
            text=f"{message} | Messages: {stats['total_messages']} | Duration: {stats['duration']}")
    
    def show_about(self):
        about_text = """ChatBuddy Pro v2.0 🤖
────────────────────────
An advanced chatbot with professional features:
• Smart conversation memory
• Sentiment analysis
• File attachments
• Multiple themes
• Chat history & export
• Session management
• Typing indicators
• Auto-complete suggestions
• Notifications
────────────────────────
Created with Python & Tkinter
© 2024 ChatBuddy Pro"""
        
        messagebox.showinfo("About ChatBuddy Pro", about_text)
    
    def show_help(self):
        help_text = """📚 ChatBuddy Pro Help
────────────────────────
Basic Commands:
• hello/hi - Greet the bot
• how are you - Check bot's mood
• tell me a joke - Get a funny joke
• what time is it - Current time
• help - Show this help
• goodbye - End conversation

Advanced Features:
1. Attach Files: Click 📎 button
2. Analyze Mood: Click 'Analyze Mood' button
3. Export Chat: File → Export Chat
4. Change Theme: Edit → Themes
5. View Stats: View → Session Stats
6. Clear Chat: Click 'Clear Chat' button

Tips:
• Press Tab for auto-complete
• Press Enter to send message
• Right-click for context menu
• Sessions auto-save every 30s"""
        
        messagebox.showinfo("Help Guide", help_text)
    
    def run(self):
        self.root.mainloop()

# -------------------- Main Execution -------------------- #
if __name__ == "__main__":
    print("Starting ChatBuddy Pro...")
    print("Features included:")
    print("✓ Enhanced UI with themes")
    print("✓ Chat history & logging")
    print("✓ Typing indicators")
    print(f"✓ Sentiment analysis: {'Enabled' if SENTIMENT_ANALYSIS else 'Disabled (install textblob)'}")
    print(f"✓ Notifications: {'Enabled' if NOTIFICATIONS else 'Disabled (install plyer)'}")
    print("✓ File attachments")
    print("✓ Session management")
    print("✓ Auto-complete suggestions")
    print("✓ Export & save features")
    print("\nFor best experience, install: pip install textblob plyer\n")
    
    app = ChatBuddyPro()
    app.run()
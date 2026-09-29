import re
import random

# 定义规则库:模式(正则表达式) -> 响应模板列表
rules = {
    r'\bI work as (?:an? )?(.+?)[.!?]?\s*$': [
        "What do you enjoy about working as {0}?",
        "What has been challenging about your work as {0}?"
    ],
    r'\bI work (?:at|in) (.+?)[.!?]?\s*$': [
        "How do you feel about working at or in {0}?",
        "What is a typical day like for you at {0}?"
    ],
    r'\bI (?:study|am studying) (.+?)[.!?]?\s*$': [
        "What interests you most about studying {0}?",
        "How is studying {0} going for you?"
    ],
    r'\bI (?:like|enjoy|love) (.+?)[.!?]?\s*$': [
        "What do you enjoy most about {0}?",
        "How did you become interested in {0}?"
    ],
    r'I need (.*)': [
        "Why do you need {0}?",
        "Would it really help you to get {0}?",
        "Are you sure you need {0}?"
    ],
    r'Why don\'t you (.*)\?': [
        "Do you really think I don't {0}?",
        "Perhaps eventually I will {0}.",
        "Do you really want me to {0}?"
    ],
    r'Why can\'t I (.*)\?': [
        "Do you think you should be able to {0}?",
        "If you could {0}, what would you do?",
        "I don't know -- why can't you {0}?"
    ],
    r'I am (.*)': [
        "Did you come to me because you are {0}?",
        "How long have you been {0}?",
        "How do you feel about being {0}?"
    ],
    r'.* mother .*': [
        "Tell me more about your mother.",
        "What was your relationship with your mother like?",
        "How do you feel about your mother?"
    ],
    r'.* father .*': [
        "Tell me more about your father.",
        "How did your father make you feel?",
        "What has your father taught you?"
    ],
    r'.*': [
        "Please tell me more.",
        "Let's change focus a bit... Tell me about your family.",
        "Can you elaborate on that?"
    ]
}

# 本次运行期间的对话记忆；退出程序后不会保留
conversation_memory = {}


def remember(user_input, memory):
    """只记录用户明确提供的姓名、年龄和职业。"""
    name = re.search(r'\b(?:my name is|call me)\s+([A-Za-z][A-Za-z\'-]*)',
                     user_input, re.IGNORECASE)
    age = re.search(r"\b(?:I am|I'm)\s+(\d{1,3})\s+years old\b",
                    user_input, re.IGNORECASE)
    occupation = re.search(r'\b(?:I work as|my job is)\s+(?:an?\s+)?'
                           r'([A-Za-z][A-Za-z -]*?)(?=[.!?]|$)',
                           user_input, re.IGNORECASE)
    if name:
        memory['name'] = name.group(1)
    if age:
        memory['age'] = age.group(1)
    if occupation:
        memory['occupation'] = occupation.group(1).strip()


def recall(memory):
    """回答用户关于已记录信息的提问。"""
    facts = []
    if memory.get('name'):
        facts.append(f"your name is {memory['name']}")
    if memory.get('age'):
        facts.append(f"you are {memory['age']} years old")
    if memory.get('occupation'):
        facts.append(f"you work as {memory['occupation']}")
    return "I remember that " + ", and ".join(facts) + "." if facts else \
        "You haven't told me your name, age, or occupation yet."

# 定义代词转换规则
pronoun_swap = {
    "i": "you", "you": "i", "me": "you", "my": "your",
    "am": "are", "are": "am", "was": "were", "i'd": "you would",
    "i've": "you have", "i'll": "you will", "yours": "mine",
    "mine": "yours"
}


def swap_pronouns(phrase):
    """
    对输入短语中的代词进行第一/第二人称转换
    """
    words = phrase.lower().split()
    swapped_words = [pronoun_swap.get(word, word) for word in words]
    return " ".join(swapped_words)


def respond(user_input, memory=None):
    """
    根据规则库生成响应
    """
    if memory is None:
        memory = conversation_memory
    remember(user_input, memory)

    if re.search(r'\b(?:what do you remember about me|do you remember me|'
                 r'what is my (?:name|age|job))\b', user_input, re.IGNORECASE):
        return recall(memory)

    if re.search(r'\b(?:my name is|call me)\b', user_input, re.IGNORECASE) and memory.get('name'):
        return f"Nice to meet you, {memory['name']}. What would you like to talk about?"
    if re.search(r"\b(?:I am|I'm)\s+\d{1,3}\s+years old\b", user_input, re.IGNORECASE):
        return "How do you feel about this stage of your life?"

    for pattern, responses in rules.items():
        if pattern == r'.*':
            continue
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            # 捕获匹配到的部分
            captured_group = match.group(1) if match.groups() else ''
            # 进行代词转换
            swapped_group = swap_pronouns(captured_group)
            # 从模板中随机选择一个并格式化
            response = random.choice(responses).format(swapped_group)
            return response
    # 在普通规则没有命中时，优先引用已记住的信息
    if memory.get('occupation'):
        return f"You mentioned working as {memory['occupation']}. How has that been going?"
    if memory.get('name'):
        return f"Tell me more about that, {memory['name']}."
    if memory.get('age'):
        return f"You mentioned being {memory['age']}. How does that relate to what you just said?"
    return random.choice(rules[r'.*'])


# 主聊天循环
if __name__ == '__main__':
    print("Therapist: Hello! How can I help you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Therapist: Goodbye. It was nice talking to you.")
            break
        response = respond(user_input)
        print(f"Therapist: {response}")


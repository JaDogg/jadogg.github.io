---
title: "Designing a new programming language"
summary: "About programming languages and why I'm creating a new one."
date: 2022-01-23
tags:
  - yaksha
  - language-design
---

Advantage of creating a new programming languages is that you can start from scratch. You also get to sweeten it yourself and to the right amount.

---

📝<small>
Programming languages sweeten over time. - [Crafting Interpreters](https://craftinginterpreters.com/control-flow.html#design-note)
</small>

---



#  How do you avoid weird quirks?
Unpredictability in languages confuse new developers. Additionally, to borrow from zen of python, explicit is better than implicit.

---

📝<small>
Being pure to the language's own philosophy is hard work.
</small>

---

It is often things that are implicit that makes it harder to reason with a language. If it is harder to reason with then, it is a quirk. I think it is better to have some amount of implicit things if it is convenient.
I believe it is usually better to not go overboard with this.Explicit is where languages like Java shines. However, at some-point highly explicit languages code becomes too boilerplate like.

---

📝<small>
More fluff and less stuff.
</small>

---



#  Object-oriented programming is pure fluff
Object-oriented programming does not add to what your code does. Which makes it fall into fluff kind-of category. But it is also a way to abstract away complexity. Which makes it sometimes useful. But like any tool it has its own advantages and disadvantages. If the compiler is not smart, extra indirections just make the program slower.I believe having freestanding functions in a language is a good thing.

---

📝<small>
Do you really need a `class` to `print` hello world?
</small>

---

Some languages even allows having code outside of functions. Even though this makes a hello-world simpler, I often wonder where does the code start to execute from?.

---

📝<small>
I draw the line at `main()` function.
</small>

---



#  Why one should build a programming language?
* You can define the level of flexibility in your language.
* It is nothing but pure fun.
* Improve your design and planning skills.
* Rules are meant to be broken.
* Solve problems that are hard or annoying to solve with languages you have now.

---

📝<small>
It is also a very good programming challenge.
</small>

---


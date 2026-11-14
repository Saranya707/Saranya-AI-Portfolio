'use strict';

// Mobile navigation
const menuToggle = document.querySelector('.menu-toggle');
const navLinks = document.querySelector('.nav-links');
menuToggle.addEventListener('click', () => {
  const isOpen = navLinks.classList.toggle('open');
  menuToggle.setAttribute('aria-expanded', String(isOpen));
  menuToggle.textContent = isOpen ? '×' : '☰';
});
navLinks.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
  navLinks.classList.remove('open');
  menuToggle.setAttribute('aria-expanded', 'false');
  menuToggle.textContent = '☰';
}));

// Project category filters
const filterButtons = document.querySelectorAll('.filter');
const projectCards = document.querySelectorAll('.project-card');
filterButtons.forEach(button => button.addEventListener('click', () => {
  const category = button.dataset.filter;
  filterButtons.forEach(item => {
    const selected = item === button;
    item.classList.toggle('active', selected);
    item.setAttribute('aria-pressed', String(selected));
  });
  projectCards.forEach(card => {
    card.hidden = category !== 'all' && !card.dataset.category.split(' ').includes(category);
  });
}));

// The frontend and API are served from the same origin by FastAPI.
const contactForm = document.querySelector('#contact-form');
contactForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!contactForm.reportValidity()) return;
  const status = document.querySelector('#form-status');
  const button = contactForm.querySelector('button[type="submit"]');
  button.disabled = true;
  status.textContent = 'Sending your message...';
  try {
    const response = await fetch('/api/contact', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        name: document.querySelector('#name').value.trim(),
        email: document.querySelector('#email').value.trim(),
        message: document.querySelector('#message').value.trim()
      })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Unable to send message');
    status.textContent = 'Message received! Thank you for reaching out.';
    contactForm.reset();
  } catch (error) {
    status.textContent = 'Could not send: ' + error.message + '. Check that the FastAPI server is running.';
  } finally { button.disabled = false; }
});

const launcher = document.querySelector('#chat-launcher');
const panel = document.querySelector('#chat-panel');
const closeChat = document.querySelector('#chat-close');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');
const messages = document.querySelector('#chat-messages');
function toggleChat(open) {
  panel.hidden = !open;
  launcher.setAttribute('aria-expanded', String(open));
  if (open) chatInput.focus(); else launcher.focus();
}
launcher.addEventListener('click', () => toggleChat(panel.hidden));
closeChat.addEventListener('click', () => toggleChat(false));
function addMessage(text, className) {
  const bubble = document.createElement('div');
  bubble.className = className;
  bubble.textContent = text;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}
chatForm.addEventListener('submit', async event => {
  event.preventDefault();
  const question = chatInput.value.trim();
  if (!question) return;
  addMessage(question, 'user-msg');
  chatInput.value = '';
  const waiting = addMessage('Thinking...', 'bot-msg');
  const button = chatForm.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: question})
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Chat unavailable');
    waiting.textContent = result.reply;
  } catch (error) {
    waiting.textContent = 'Could not reach the assistant. Start the FastAPI server and refresh.';
  } finally { button.disabled = false; chatInput.focus(); }
});
document.querySelector('#year').textContent = new Date().getFullYear();

async function askPortfolioAI(message) {
    const response = await fetch("/api/ai-chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message })
    });

    if (!response.ok) {
        throw new Error("AI chatbot request failed");
    }

    const data = await response.json();
    return data.reply;
}

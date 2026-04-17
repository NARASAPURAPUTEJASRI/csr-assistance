const chat = document.getElementById('chat');
const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');

function addMessage(text, isUser = false) {
  const msg = document.createElement('div');
  msg.className = `flex ${isUser ? 'justify-end' : 'justify-start'}`;
  msg.innerHTML = `
    <div class="${isUser ? 'bg-blue-600' : 'bg-slate-700'} max-w-[80%] px-5 py-3 rounded-3xl rounded-br-none">
      <p class="text-sm whitespace-pre-line">${text.replace(/\n/g, '<br>')}</p>
      <span class="text-xs opacity-70 mt-1 block">${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
    </div>
  `;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = input.value.trim();
  if (!query) return;

  addMessage(query, true);
  input.value = '';

  const typing = document.createElement('div');
  typing.id = 'typing';
  typing.className = 'flex justify-start';
  typing.innerHTML = `<div class="bg-slate-700 px-5 py-3 rounded-3xl">AI is thinking<span class="animate-pulse">...</span></div>`;
  chat.appendChild(typing);
  chat.scrollTop = chat.scrollHeight;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    typing.remove();
    addMessage(data.response);
  } catch (err) {
    typing.remove();
    addMessage("Sorry, I'm having trouble connecting right now.");
  }
});

window.onload = () => {
  addMessage("Hello! I'm your AI Customer Assistant.<br>How can I help you today?");
};
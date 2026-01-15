import React, { useState } from 'react'
import axios from 'axios'

export default function Chat({apiUrl, token, onLogout}){
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')

  const send = async ()=>{
    if(!input) return
    const userMsg = {role: 'user', content: input}
    setMessages(prev=>[...prev, {from: 'user', text: input}])
    setInput('')
    try{
      const res = await axios.post(apiUrl + '/chat', { message: userMsg.content }, { headers: { Authorization: `Bearer ${token}` } })
      setMessages(prev=>[...prev, {from: 'assistant', text: res.data.reply}])
    }catch(e){
      setMessages(prev=>[...prev, {from:'assistant', text: 'Error del servidor o de autenticación.'}])
    }
  }

  return (
    <div className="chat">
      <div className="controls">
        <button onClick={onLogout}>Cerrar sesión</button>
      </div>
      <div className="messages">
        {messages.map((m,i)=>(
          <div key={i} className={`msg ${m.from}`}>
            <pre>{m.text}</pre>
          </div>
        ))}
      </div>
      <div className="composer">
        <textarea value={input} onChange={e=>setInput(e.target.value)} placeholder="Escribe tu consulta técnica..." />
        <button onClick={send}>Enviar</button>
      </div>
    </div>
  )
}

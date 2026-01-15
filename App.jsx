import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Chat from './components/Chat'
import Admin from './components/Admin'

const API = (import.meta.env.VITE_API_URL) ? import.meta.env.VITE_API_URL : 'http://localhost:8000'

export default function App(){
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [isAdmin, setIsAdmin] = useState(false)
  const [view, setView] = useState('chat')

  const handleSaveToken = (t)=>{
    localStorage.setItem('token', t)
    setToken(t)
  }

  useEffect(()=>{
    if(!token){
      setIsAdmin(false)
      return
    }
    (async ()=>{
      try{
        const res = await axios.get(API + '/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        setIsAdmin(!!res.data.is_admin)
      }catch(e){
        setIsAdmin(false)
      }
    })()
  }, [token])

  return (
    <div className="app">
      <header><h1>Chatbot técnico (ES)</h1></header>
      {!token ? (
        <Auth onSaveToken={handleSaveToken} apiUrl={API} />
      ) : (
        <div>
          <div style={{marginBottom:8}}>
            <button onClick={()=>setView('chat')}>Chat</button>
            {isAdmin && <button onClick={()=>setView('admin')}>Admin</button>}
            <button onClick={()=>{localStorage.removeItem('token'); setToken(''); setIsAdmin(false)}}>Cerrar sesión</button>
          </div>
          {view === 'chat' && <Chat apiUrl={API} token={token} />}
          {view === 'admin' && isAdmin && <Admin apiUrl={API} token={token} />}
        </div>
      )}
    </div>
  )
}

function Auth({onSaveToken, apiUrl}){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const login = async ()=>{
    const data = new URLSearchParams()
    data.append('username', username)
    data.append('password', password)
    try{
      const res = await axios.post(apiUrl + '/auth/token', data)
      onSaveToken(res.data.access_token)
    }catch(e){
      alert('Login falló')
    }
  }

  const register = async ()=>{
    try{
      await axios.post(apiUrl + '/auth/register', null, { params: { username, password }})
      alert('Usuario creado. Ahora inicia sesión.')
    }catch(e){
      alert('Registro falló')
    }
  }

  return (
    <div className="auth">
      <input placeholder="Usuario" value={username} onChange={e=>setUsername(e.target.value)} />
      <input placeholder="Contraseña" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
      <div className="buttons">
        <button onClick={login}>Iniciar sesión</button>
        <button onClick={register}>Registrarse</button>
      </div>
    </div>
  )
}

import React, { useState, useEffect } from 'react'
import axios from 'axios'

export default function Admin({apiUrl, token}){
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(10)
  const [total, setTotal] = useState(0)
  const [q, setQ] = useState('')
  const [userFilter, setUserFilter] = useState('')

  const fetchReports = async (p = page) =>{
    setLoading(true)
    try{
      const params = { page: p, size, q }
      if(userFilter) params.user = userFilter
      const res = await axios.get(apiUrl + '/admin/reports', { params, headers: { Authorization: `Bearer ${token}` } })
      setReports(res.data.items)
      setTotal(res.data.total || 0)
      setPage(res.data.page || p)
    }catch(e){
      alert('No se pudo obtener reportes. ¿Eres admin?')
    }finally{setLoading(false)}
  }

  const clearReports = async ()=>{
    if(!confirm('Limpiar todos los reportes?')) return
    try{
      await axios.post(apiUrl + '/admin/reports/clear', {}, { headers: { Authorization: `Bearer ${token}` } })
      setReports([])
      setTotal(0)
      alert('Reportes eliminados')
    }catch(e){
      alert('Error al limpiar reportes')
    }
  }

  useEffect(()=>{ fetchReports(1) }, [size])

  const onSearch = async ()=>{ fetchReports(1) }

  const nextPage = ()=>{ if(page * size < total) fetchReports(page+1) }
  const prevPage = ()=>{ if(page > 1) fetchReports(page-1) }

  return (
    <div>
      <h2>Panel de reportes</h2>
      <div style={{marginBottom:8}}>
        <input placeholder="Buscar texto" value={q} onChange={e=>setQ(e.target.value)} />
        <input placeholder="Usuario" value={userFilter} onChange={e=>setUserFilter(e.target.value)} style={{marginLeft:8}} />
        <button onClick={onSearch} style={{marginLeft:8}}>Buscar</button>
        <button onClick={()=>{ setQ(''); setUserFilter(''); fetchReports(1) }} style={{marginLeft:8}}>Limpiar filtros</button>
        <button onClick={() => fetchReports(1)} style={{marginLeft:8}}>Refrescar</button>
        <button onClick={clearReports} style={{marginLeft:8}}>Limpiar reportes</button>
      </div>

      <div style={{marginBottom:8}}>
        <label>Items por página: </label>
        <select value={size} onChange={e=>setSize(Number(e.target.value))}>
          <option value={5}>5</option>
          <option value={10}>10</option>
          <option value={20}>20</option>
        </select>
      </div>

      {loading && <div>Cargando...</div>}
      {!loading && reports.length === 0 && <div>No hay reportes.</div>}

      <div>
        {reports.map((r)=> (
          <div key={r.id} style={{border:'1px solid #ddd', padding:8, marginBottom:6}}>
            <div><strong>Usuario:</strong> {r.user}</div>
            <div><strong>Fecha:</strong> {r.timestamp}</div>
            <div><strong>Razón:</strong> {r.reason}</div>
            <div><strong>Categoría:</strong> {r.category}</div>
            <pre style={{whiteSpace:'pre-wrap'}}>{r.message}</pre>
          </div>
        ))}
      </div>

      <div style={{marginTop:12}}>
        <button onClick={prevPage} disabled={page<=1}>Anterior</button>
        <span style={{margin:'0 8px'}}>Página {page} — Total {total}</span>
        <button onClick={nextPage} disabled={page*size>=total}>Siguiente</button>
      </div>
    </div>
  )
}

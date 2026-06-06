import React from 'react'
import TopBar from './TopBar'
import Sidebar from './Sidebar'

export default function Layout({ children, documents = [] }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <TopBar />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar documents={documents} />
        <main
          style={{
            flex: 1,
            display: 'flex',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {children}
        </main>
      </div>
    </div>
  )
}

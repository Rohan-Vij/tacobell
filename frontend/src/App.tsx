import { useState } from 'react'
import { Routes, Route } from 'react-router-dom';

import Navbar from './components/Navbar.component'
import Fullscreen from './components/Fullscreen.component'

import Home from './pages/Home.page';

import './App.css';

function App() {

  return (
    <>
      <Navbar />

      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </>
  )
}

export default App

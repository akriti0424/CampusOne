import { useEffect, useMemo, useRef, useState } from 'react'

import { api } from './api'
import AdminDashboard from './components/AdminDashboard'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const initialProduct = {
  title: '',
  description: '',
  price: '',
  category: 'Hostel Items',
  negotiable: true,
  image_url: '',
}

const initialLostFound = {
  title: '',
  description: '',
  location: '',
  image_url: '',
  kind: 'lost',
}

const initialChat = {
  room_name: 'general',
  message: '',
}

const APP_STEPS = [
  'Email-verified access',
  'Buy & sell listings',
  'Private lost-and-found matching',
  'Anonymous community chat',
]

const MODULES = [
  { icon: '↗', label: 'Marketplace', title: 'Buy and sell', copy: 'Post student listings with seller privacy and negotiable pricing.' },
  { icon: '⌕', label: 'Lost and found', title: 'Private matching', copy: 'Store reports privately and verify desk handoff with OTP.' },
  { icon: '◌', label: 'Chat', title: 'Live community room', copy: 'Join a realtime room for helpful campus conversation.' },
]

export default function App() {
  const socketRef = useRef(null)
  const [view, setView] = useState('dashboard')
  const [authMode, setAuthMode] = useState('login')
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [registerForm, setRegisterForm] = useState({ full_name: '', scholar_id: '', branch: '', email: '', password: '' })
  const [otpForm, setOtpForm] = useState({ email: '', otp: '' })
  const [session, setSession] = useState(() => {
    const token = localStorage.getItem('campusone_token')
    const user = localStorage.getItem('campusone_user')
    return {
      token,
      user: user ? JSON.parse(user) : null,
    }
  })
  const [status, setStatus] = useState('')
  const [products, setProducts] = useState([])
  const [productForm, setProductForm] = useState(initialProduct)
  const [lostFoundForm, setLostFoundForm] = useState(initialLostFound)
  const [lostItems, setLostItems] = useState([])
  const [matches, setMatches] = useState([])
  const [verificationForm, setVerificationForm] = useState({ item_id: '', verification_code: '', desk_notes: '' })
  const [chatForm, setChatForm] = useState(initialChat)
  const [messages, setMessages] = useState([])
  const [chatStatus, setChatStatus] = useState('offline')

  const stats = useMemo(
    () => [
      { label: 'Marketplace', value: products.length },
      { label: 'Private reports', value: lostItems.length },
      { label: 'Match leads', value: matches.length },
      { label: 'Chat messages', value: messages.length },
    ],
    [products.length, lostItems.length, matches.length, messages.length],
  )

  useEffect(() => {
    if (session.token) {
      loadPublicData()
    }
  }, [])

  useEffect(() => {
    if (!session.token) {
      setLostItems([])
      setMatches([])
      setMessages([])
      setChatStatus('offline')
      return
    }

    Promise.all([loadProfile(), loadPrivateData()]).catch((error) => setStatus(error.message))
  }, [session.token])

  useEffect(() => {
    if (!session.token) {
      return undefined
    }

    let cancelled = false
    const wsProtocol = API_URL.startsWith('https') ? 'wss' : 'ws'
    const socketUrl = `${API_URL.replace(/^https?/, wsProtocol)}/api/chat/ws/${encodeURIComponent(chatForm.room_name)}?token=${encodeURIComponent(session.token)}`

    async function openSocket() {
      try {
        const history = await api.listChatMessages(session.token, chatForm.room_name)
        if (cancelled) return
        setMessages(history)

        const socket = new WebSocket(socketUrl)
        socketRef.current = socket

        socket.onopen = () => setChatStatus('live')
        socket.onclose = () => setChatStatus('offline')
        socket.onerror = () => setChatStatus('error')
        socket.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data)
            if (payload.type === 'history' && Array.isArray(payload.messages)) {
              setMessages(payload.messages)
              return
            }

            if (payload.type === 'message' && payload.message) {
              setMessages((current) => [...current, payload.message])
            }
          } catch (error) {
            setStatus(error.message)
          }
        }
      } catch (error) {
        setChatStatus('offline')
        setStatus(error.message)
      }
    }

    openSocket()

    return () => {
      cancelled = true
      if (socketRef.current) {
        socketRef.current.close()
        socketRef.current = null
      }
    }
  }, [session.token, chatForm.room_name])

  async function loadPublicData() {
    try {
      const productList = await api.listProducts()
      setProducts(productList)
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function loadProfile() {
    if (!session.token) return
    const profile = await api.me(session.token)
    setSession((current) => ({ ...current, user: profile }))
    localStorage.setItem('campusone_user', JSON.stringify(profile))
  }

  async function loadPrivateData() {
    const [items, matchList] = await Promise.all([
      api.listLostFound(session.token),
      api.listMatches(session.token),
    ])
    setLostItems(items)
    setMatches(matchList)
  }

  function onLoginChange(event) {
    const { name, value } = event.target
    setLoginForm((current) => ({ ...current, [name]: value }))
  }

  function onRegisterChange(event) {
    const { name, value } = event.target
    setRegisterForm((current) => ({ ...current, [name]: value }))
  }

  function onOtpChange(event) {
    const { name, value } = event.target
    setOtpForm((current) => ({ ...current, [name]: value }))
  }

  function onProductChange(event) {
    const { name, value, type, checked } = event.target
    setProductForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  function onLostFoundChange(event) {
    const { name, value } = event.target
    setLostFoundForm((current) => ({ ...current, [name]: value }))
  }

  function onChatChange(event) {
    const { name, value } = event.target
    setChatForm((current) => ({ ...current, [name]: value }))
  }

  function onVerificationChange(event) {
    const { name, value } = event.target
    setVerificationForm((current) => ({ ...current, [name]: value }))
  }

  async function handleLoginSubmit(event) {
    event.preventDefault()
    setStatus('')

    try {
      const response = await api.login(loginForm)

      localStorage.setItem('campusone_token', response.token.access_token)
      localStorage.setItem('campusone_user', JSON.stringify(response.user))
      setSession({ token: response.token.access_token, user: response.user })
      setView('dashboard')
      setStatus(`Welcome, ${response.user.full_name.split(' ')[0]}.`)
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function handleRegisterSubmit(event) {
    event.preventDefault()
    setStatus('')
    try {
      const response = await api.register(registerForm)
      setOtpForm({ email: response.email, otp: '' })
      setAuthMode('verify')
      setStatus('A six-digit verification code was sent to your campus email.')
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function handleVerifyEmail(event) {
    event.preventDefault()
    setStatus('')
    try {
      const response = await api.verifyEmail(otpForm)
      localStorage.setItem('campusone_token', response.token.access_token)
      localStorage.setItem('campusone_user', JSON.stringify(response.user))
      setSession({ token: response.token.access_token, user: response.user })
      setView('dashboard')
      setStatus('Email verified. Welcome to CampusOne!')
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function handleResendOtp() {
    try {
      await api.resendVerification(otpForm.email)
      setStatus('A new verification code was sent.')
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function handleCreateProduct(event) {
    event.preventDefault()
    try {
      await api.createProduct(session.token, {
        ...productForm,
        price: Number(productForm.price),
      })
      setProductForm(initialProduct)
      await loadPublicData()
      setStatus('Marketplace listing published.')
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function handleCreateLostFound(event) {
    event.preventDefault()
    try {
      await api.createLostFound(session.token, lostFoundForm)
      setLostFoundForm(initialLostFound)
      await loadPrivateData()
      setStatus('Lost/found report submitted privately.')
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function handleRequestVerification(itemId) {
    try {
      const response = await api.requestLostFoundVerification(session.token, itemId)
      await loadPrivateData()
      setStatus(`Verification code generated for item ${response.item_id}: ${response.verification_code}`)
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function handleResolveItem(itemId) {
    try {
      await api.resolveLostFound(session.token, itemId)
      await loadPrivateData()
      setStatus(`Lost/found item ${itemId} resolved successfully.`)
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function handleVerificationAction(event, action) {
    event.preventDefault()

    try {
      const itemId = Number(verificationForm.item_id)
      if (!itemId) {
        throw new Error('Enter a valid item ID')
      }

      if (action === 'verify') {
        await api.verifyLostFound(session.token, itemId, {
          verification_code: verificationForm.verification_code,
          desk_notes: verificationForm.desk_notes || null,
        })
      }

      if (action === 'resolve') {
        await api.resolveLostFound(session.token, itemId)
      }

      if (action === 'close') {
        await api.closeLostFound(session.token, itemId)
      }

      setVerificationForm({ item_id: '', verification_code: '', desk_notes: '' })
      await loadPrivateData()
      setStatus(`Lost/found item ${action}d successfully.`)
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function handleSendMessage(event) {
    event.preventDefault()
    try {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ message: chatForm.message }))
      } else {
        await api.sendChatMessage(session.token, chatForm)
        const roomMessages = await api.listChatMessages(session.token, chatForm.room_name)
        setMessages(roomMessages)
      }
      setChatForm((current) => ({ ...current, message: '' }))
      setStatus('Message posted to the room.')
    } catch (error) {
      setStatus(error.message)
    }
  }

  function logout() {
    localStorage.removeItem('campusone_token')
    localStorage.removeItem('campusone_user')
    setSession({ token: null, user: null })
    setLostItems([])
    setMatches([])
    setMessages([])
    setChatStatus('offline')
    setView('dashboard')
  }

  const isAdmin = session.user?.role === 'admin'
  const isLoggedIn = Boolean(session.token)

  return (
    <div className="shell">
      <div className="backdrop backdrop-a" />
      <div className="backdrop backdrop-b" />

      <header className="topbar">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">C</span>
          <div>
            <p className="eyebrow">MANIT campus platform</p>
            <h1>CampusOne</h1>
          </div>
        </div>
        <div className="topbar-actions">
          {isLoggedIn ? (
            <div className="segmented compact-nav">
              <button className={view === 'dashboard' ? 'active' : ''} type="button" onClick={() => setView('dashboard')}>
                Dashboard
              </button>
              {isAdmin ? <button className={view === 'admin' ? 'active' : ''} type="button" onClick={() => setView('admin')}>Admin</button> : null}
            </div>
          ) : null}
          {session.user ? <span className="chip">{session.user.full_name}</span> : <span className="chip muted">Guest</span>}
          {session.token ? (
            <button className="button button-ghost" type="button" onClick={logout}>
              Sign out
            </button>
          ) : null}
        </div>
      </header>

      <main className="layout">
        {!isLoggedIn ? (
          <section className="hero card landing-hero">
            <div className="hero-copy">
              <p className="eyebrow">MANIT campus platform</p>
              <h2>Verify your campus email, then unlock every module.</h2>
              <p className="hero-text">
                CampusOne is a clean, modern student platform for buying, lost-and-found, and anonymous chat. New
                accounts are activated with a code sent to their campus email.
              </p>
              <div className="step-row">
                {APP_STEPS.map((step) => (
                  <span key={step} className="step-pill">
                    {step}
                  </span>
                ))}
              </div>
              <div className="landing-proof">
                <span><b>01</b> Campus email</span>
                <span><b>02</b> OTP verified</span>
                <span><b>03</b> Ready to connect</span>
              </div>
            </div>

            <div className="login-panel card-inner">
              <div className="section-head login-head">
                <div>
                  <p className="eyebrow">Secure access</p>
                  <h3>{authMode === 'login' ? 'Sign in' : authMode === 'register' ? 'Create account' : 'Verify email'}</h3>
                </div>
              </div>

              <div className="auth-tabs" aria-label="Authentication options">
                <button className={authMode === 'login' ? 'active' : ''} type="button" onClick={() => setAuthMode('login')}>Sign in</button>
                <button className={authMode === 'register' ? 'active' : ''} type="button" onClick={() => setAuthMode('register')}>Create account</button>
              </div>

              {authMode === 'login' ? (
                <form className="form" onSubmit={handleLoginSubmit}>
                  <Field label="Campus email" name="email" type="email" value={loginForm.email} onChange={onLoginChange} />
                  <Field label="Password" name="password" type="password" value={loginForm.password} onChange={onLoginChange} />
                  <button className="button button-primary" type="submit">Login to dashboard <span>→</span></button>
                  <button className="text-button" type="button" onClick={() => setAuthMode('register')}>New to CampusOne? Create an account</button>
                </form>
              ) : authMode === 'register' ? (
                <form className="form" onSubmit={handleRegisterSubmit}>
                  <Field label="Full name" name="full_name" value={registerForm.full_name} onChange={onRegisterChange} required />
                  <div className="inline-grid">
                    <Field label="Scholar ID" name="scholar_id" value={registerForm.scholar_id} onChange={onRegisterChange} required />
                    <Field label="Branch" name="branch" value={registerForm.branch} onChange={onRegisterChange} required />
                  </div>
                  <Field label="Campus email" name="email" type="email" value={registerForm.email} onChange={onRegisterChange} required />
                  <Field label="Password" name="password" type="password" minLength="8" value={registerForm.password} onChange={onRegisterChange} required />
                  <button className="button button-primary" type="submit">Send verification code <span>→</span></button>
                  <button className="text-button" type="button" onClick={() => setAuthMode('login')}>Already have an account? Sign in</button>
                </form>
              ) : (
                <form className="form" onSubmit={handleVerifyEmail}>
                  <Field label="Campus email" name="email" type="email" value={otpForm.email} onChange={onOtpChange} required />
                  <Field label="Six-digit code" name="otp" inputMode="numeric" pattern="[0-9]{6}" maxLength="6" value={otpForm.otp} onChange={onOtpChange} required />
                  <button className="button button-primary" type="submit">Verify and continue <span>→</span></button>
                  <div className="auth-actions">
                    <button className="text-button" type="button" onClick={handleResendOtp}>Resend code</button>
                    <button className="text-button" type="button" onClick={() => setAuthMode('login')}>Back to login</button>
                  </div>
                </form>
              )}

              <p className="helper auth-helper"><span>✓</span> Only verified @stu.manit.ac.in accounts can sign in.</p>
              {status ? <p className="status">{status}</p> : null}
            </div>
          </section>
        ) : view === 'admin' && isAdmin ? (
          <AdminDashboard
            lostItems={lostItems}
            matches={matches}
            verificationForm={verificationForm}
            onVerificationChange={onVerificationChange}
            onVerify={(event) => handleVerificationAction(event, 'verify')}
            onResolve={handleResolveItem}
            onClose={(event) => handleVerificationAction(event, 'close')}
            onRequestVerification={handleRequestVerification}
            status={status}
          />
        ) : (
          <>
            <section className="hero card dashboard-hero">
              <div className="hero-copy">
                <p className="eyebrow">Campus dashboard</p>
                <h2>All modules in one place.</h2>
                <p className="hero-text">
                  Open the marketplace, lost-and-found, and live chat from a single modern workspace.
                </p>
              </div>

              <div className="stats-grid">
                {stats.map((stat) => (
                  <article className="stat-card" key={stat.label}>
                    <span>{stat.label}</span>
                    <strong>{stat.value}</strong>
                  </article>
                ))}
              </div>
            </section>

            <section className="modules-grid">
              {MODULES.map((module) => (
                <article className="module-card card" key={module.label}>
                  <span className="module-icon" aria-hidden="true">{module.icon}</span>
                  <p className="eyebrow">{module.label}</p>
                  <h3>{module.title}</h3>
                  <p className="hero-text">{module.copy}</p>
                </article>
              ))}

              {isAdmin ? (
                <article className="module-card card admin-callout">
                  <p className="eyebrow">Admin</p>
                  <h3>Desk dashboard</h3>
                  <p className="hero-text">Review matches, verify OTPs, and close resolved cases.</p>
                </article>
              ) : null}
            </section>

            <section className="grid two-col">
              <article className="card auth-card">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Session</p>
                    <h3>Secure JWT state</h3>
                  </div>
                </div>
                <div className="profile-panel">
                  <span className="avatar">{session.user ? session.user.full_name.slice(0, 1) : 'C'}</span>
                  <div>
                    <strong>{session.user ? session.user.full_name : 'Guest user'}</strong>
                    <p>{session.user ? `${session.user.branch} • ${session.user.email}` : 'Sign in to unlock private tools.'}</p>
                  </div>
                </div>
                <div className="notice">
                  <strong>Access</strong>
                  <p>Login → JWT token → authenticated modules.</p>
                </div>
                {status ? <p className="status">{status}</p> : null}
              </article>

              <article className="card quick-links-card">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Quick actions</p>
                    <h3>Jump to a module</h3>
                  </div>
                </div>
                <div className="quick-links">
                  <button className="button button-ghost" type="button" onClick={() => setView('dashboard')}>
                    Dashboard
                  </button>
                  {isAdmin ? (
                    <button className="button button-secondary" type="button" onClick={() => setView('admin')}>
                      Open admin desk
                    </button>
                  ) : null}
                </div>
              </article>
            </section>

            <section className="grid two-col module-panels">
              <article className="card">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Marketplace</p>
                    <h3>Buy and sell with privacy-aware listings</h3>
                  </div>
                </div>

                <form className="form compact" onSubmit={handleCreateProduct}>
                  <div className="inline-grid">
                    <Field label="Title" name="title" value={productForm.title} onChange={onProductChange} />
                    <Field label="Category" name="category" value={productForm.category} onChange={onProductChange} />
                  </div>
                  <Field label="Description" name="description" value={productForm.description} onChange={onProductChange} textarea />
                  <div className="inline-grid">
                    <Field label="Price" name="price" type="number" value={productForm.price} onChange={onProductChange} />
                    <Field label="Image URL" name="image_url" value={productForm.image_url} onChange={onProductChange} />
                  </div>
                  <label className="checkbox-row">
                    <input type="checkbox" name="negotiable" checked={productForm.negotiable} onChange={onProductChange} />
                    Negotiable
                  </label>
                  <button className="button button-secondary" type="submit" disabled={!session.token}>
                    Post item
                  </button>
                </form>

                <div className="list">
                  {products.map((product) => (
                    <article className="list-card" key={product.id}>
                      <div>
                        <strong>{product.title}</strong>
                        <p>{product.description}</p>
                      </div>
                      <div className="meta-row">
                        <span>{product.category}</span>
                        <span>{product.status}</span>
                        <span>Rs. {product.price}</span>
                        <span>{product.seller_name} • {product.seller_branch}</span>
                      </div>
                    </article>
                  ))}
                </div>
              </article>

              <article className="card">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Lost and found</p>
                    <h3>Private reporting with AI-style matching</h3>
                  </div>
                </div>

                <form className="form compact" onSubmit={handleCreateLostFound}>
                  <div className="inline-grid">
                    <Field label="Title" name="title" value={lostFoundForm.title} onChange={onLostFoundChange} />
                    <Field label="Kind" name="kind" value={lostFoundForm.kind} onChange={onLostFoundChange} />
                  </div>
                  <Field label="Description" name="description" value={lostFoundForm.description} onChange={onLostFoundChange} textarea />
                  <div className="inline-grid">
                    <Field label="Location" name="location" value={lostFoundForm.location} onChange={onLostFoundChange} />
                    <Field label="Image URL" name="image_url" value={lostFoundForm.image_url} onChange={onLostFoundChange} />
                  </div>
                  <button className="button button-secondary" type="submit" disabled={!session.token}>
                    Submit private report
                  </button>
                </form>

                <div className="split-view">
                  <div>
                    <h4>My reports</h4>
                    <div className="list slim">
                      {lostItems.map((item) => (
                        <article className="list-card" key={item.id}>
                          <strong>{item.title}</strong>
                          <p>{item.location} • {item.kind} • {item.status}</p>
                          <p className="muted">Match score: {item.similarity_score}</p>
                          {item.status === 'open' ? (
                            <button className="button button-ghost" type="button" onClick={() => handleRequestVerification(item.id)}>
                              Request verification
                            </button>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4>Match leads</h4>
                    <div className="list slim">
                      {matches.map((match) => (
                        <article className="list-card" key={match.id}>
                          <strong>Source #{match.source_item_id}</strong>
                          <p>Candidate #{match.candidate_item_id}</p>
                          <p className="muted">Score: {match.score} • {match.status}</p>
                        </article>
                      ))}
                    </div>
                  </div>
                </div>
              </article>
            </section>

            <section className="card chat-card">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Anonymous community chat</p>
                  <h3>Fast campus messaging, live over WebSocket</h3>
                </div>
                <span className={`badge ${chatStatus}`}>{chatStatus}</span>
              </div>

              <form className="form chat-form" onSubmit={handleSendMessage}>
                <div className="inline-grid">
                  <Field label="Room" name="room_name" value={chatForm.room_name} onChange={onChatChange} />
                  <Field label="Message" name="message" value={chatForm.message} onChange={onChatChange} />
                </div>
                <button className="button button-primary" type="submit" disabled={!session.token}>
                  Send message
                </button>
              </form>

              <div className="message-feed">
                {messages.map((message) => (
                  <article className={`message ${message.is_system ? 'system' : ''}`} key={message.id}>
                    <div>
                      <strong>{message.display_name}</strong>
                      <p>{message.message}</p>
                    </div>
                    <span>{message.room_name}</span>
                  </article>
                ))}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}

function Field({ label, textarea = false, ...props }) {
  return (
    <label className="field">
      <span>{label}</span>
      {textarea ? <textarea rows="4" {...props} /> : <input {...props} />}
    </label>
  )
}

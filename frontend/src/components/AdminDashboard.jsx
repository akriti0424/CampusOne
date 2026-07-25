export default function AdminDashboard({
  lostItems,
  matches,
  verificationForm,
  onVerificationChange,
  onVerify,
  onResolve,
  onClose,
  onRequestVerification,
  status,
}) {
  return (
    <section className="admin-page">
      <header className="page-head card">
        <div>
          <p className="eyebrow">Admin dashboard</p>
          <h2>Desk operations, verification queue, and match review.</h2>
          <p className="hero-text">
            This page centralizes the lost-and-found workflow so the admin role has a clear place for OTP handling,
            verification, and resolution.
          </p>
        </div>

        <div className="stats-grid admin-stats">
          <article className="stat-card">
            <span>Reports</span>
            <strong>{lostItems.length}</strong>
          </article>
          <article className="stat-card">
            <span>Matches</span>
            <strong>{matches.length}</strong>
          </article>
          <article className="stat-card">
            <span>Awaiting desk</span>
            <strong>{lostItems.filter((item) => item.status === 'matched' || item.status === 'open').length}</strong>
          </article>
          <article className="stat-card">
            <span>Verified</span>
            <strong>{lostItems.filter((item) => item.status === 'verified').length}</strong>
          </article>
        </div>
      </header>

      <div className="admin-grid">
        <article className="card admin-card">
          <div className="section-head">
            <div>
              <p className="eyebrow">Verification queue</p>
              <h3>Open and matched reports</h3>
            </div>
          </div>

          <div className="list slim">
            {lostItems.map((item) => (
              <article className="list-card" key={item.id}>
                <div className="admin-item-head">
                  <strong>{item.title}</strong>
                  <span className="badge">{item.status}</span>
                </div>
                <p>{item.location} • {item.kind}</p>
                <p className="muted">Score: {item.similarity_score}</p>
                <div className="inline-actions">
                  <button className="button button-ghost" type="button" onClick={() => onRequestVerification(item.id)}>
                    Request OTP
                  </button>
                  <button className="button button-secondary" type="button" onClick={() => onResolve(item.id)}>
                    Resolve
                  </button>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="card admin-card">
          <div className="section-head">
            <div>
              <p className="eyebrow">Desk console</p>
              <h3>OTP verification and closure</h3>
            </div>
          </div>

          <form className="form compact" onSubmit={onVerify}>
            <div className="inline-grid">
              <Field label="Item ID" name="item_id" value={verificationForm.item_id} onChange={onVerificationChange} />
              <Field label="OTP" name="verification_code" value={verificationForm.verification_code} onChange={onVerificationChange} />
            </div>
            <Field label="Desk notes" name="desk_notes" value={verificationForm.desk_notes} onChange={onVerificationChange} textarea />
            <div className="inline-grid">
              <button className="button button-primary" type="submit">Verify</button>
              <button className="button button-ghost" type="button" onClick={onClose}>
                Close case
              </button>
            </div>
          </form>

          {status ? <p className="status">{status}</p> : null}
        </article>

        <article className="card admin-card">
          <div className="section-head">
            <div>
              <p className="eyebrow">Match ledger</p>
              <h3>AI suggestions and manual review</h3>
            </div>
          </div>

          <div className="list slim">
            {matches.map((match) => (
              <article className="list-card" key={match.id}>
                <strong>Source #{match.source_item_id}</strong>
                <p>Candidate #{match.candidate_item_id}</p>
                <p className="muted">Score: {match.score} • {match.status}</p>
              </article>
            ))}
          </div>
        </article>
      </div>
    </section>
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

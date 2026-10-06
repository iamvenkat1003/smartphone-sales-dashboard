export default function SectionCard({
  title,
  description,
  action,
  children,
  className = '',
}) {
  return (
    <section className={`section-card ${className}`}>
      <header className="section-header">
        <div>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
        {action}
      </header>
      {children}
    </section>
  )
}

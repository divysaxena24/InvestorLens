
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col">
      <header className="flex h-16 items-center justify-between border-b border-border bg-white px-8">
        <h1 className="text-xl font-bold tracking-tight text-primary">
          InvestorLens
        </h1>

        <span className="text-sm text-muted">
          Financial Research Intelligence
        </span>
      </header>

      <section className="flex flex-1 items-center justify-center px-6 py-20">
        <div className="max-w-3xl text-center">
          <span className="mb-5 inline-block rounded-full bg-blue-50 px-4 py-2 text-sm font-medium text-primary">
            AI-Powered Financial Intelligence
          </span>

          <h2 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
            Understand financial reports.
            <span className="text-primary"> Make sense of the numbers.</span>
          </h2>

          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-muted">
            Analyze annual reports, extract financial metrics, explore
            company performance, and ask questions backed by document
            evidence.
          </p>

          <div className="mt-10 flex justify-center gap-4">
            <button
              disabled
              className="rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-white opacity-80"
            >
              Dashboard Coming Soon
            </button>
          </div>
        </div>
      </section>

      <footer className="border-t border-border bg-white px-8 py-5 text-center text-sm text-muted">
        InvestorLens · Financial research powered by AI
      </footer>
    </main>
  );
}

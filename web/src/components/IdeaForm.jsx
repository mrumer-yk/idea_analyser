import { useState } from 'react'

export default function IdeaForm({ onSubmit, busy }) {
  const [mode, setMode] = useState('text')
  const [text, setText] = useState('')
  const [url, setUrl] = useState('')

  const submit = (e) => {
    e.preventDefault()
    if (mode === 'text') onSubmit({ input_type: 'text', raw_input: text })
    else onSubmit({ input_type: 'url', source_url: url })
  }

  const tab = (id, label) => (
    <button
      type="button"
      onClick={() => setMode(id)}
      className={`px-3 py-1.5 text-sm rounded-md ${
        mode === id ? 'bg-amber-500 text-black' : 'bg-zinc-800 text-zinc-300'
      }`}
    >
      {label}
    </button>
  )

  return (
    <form onSubmit={submit} className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
      <div className="flex gap-2 mb-3">
        {tab('text', 'Describe the idea')}
        {tab('url', 'From a URL')}
      </div>

      {mode === 'text' ? (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          placeholder="Describe your startup idea — plain text or bullets. e.g. 'A UPI-first expense tracker for Indian freelancers that auto-generates GST-ready reports.'"
          className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-sm outline-none focus:border-amber-500"
        />
      ) : (
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com  (product or competitor page)"
          className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-sm outline-none focus:border-amber-500"
        />
      )}

      <button
        type="submit"
        disabled={busy || (mode === 'text' ? !text.trim() : !url.trim())}
        className="mt-3 px-4 py-2 rounded-lg bg-amber-500 text-black font-medium text-sm disabled:opacity-40"
      >
        {busy ? 'Researching…' : 'Validate idea'}
      </button>
    </form>
  )
}

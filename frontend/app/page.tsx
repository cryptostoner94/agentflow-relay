export default async function Home() {
  return (
    <main style={{fontFamily:"system-ui", padding: 32}}>
      <h1>AgentFlow Relay</h1>
      <p>Universal agent relay and orchestration dashboard.</p>
      <ul>
        <li>Messaging adapters: Telegram, WhatsApp Cloud API, Discord, Slack</li>
        <li>BYOA: webhook, Ollama, OpenAI-compatible, MCP-style adapters</li>
        <li>Capability discovery, permission gates, execution logs</li>
      </ul>
    </main>
  );
}

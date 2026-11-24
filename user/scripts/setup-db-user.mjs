import pg from '../node_modules/.pnpm/pg@8.23.1/node_modules/pg/lib/index.js';
const { Client } = pg;

const client = new Client({
  host: '127.0.0.1',
  port: 5432,
  user: 'postgres',
  password: 'postgres',
  database: 'postgres'
});

await client.connect();
console.log('Connected to postgres as superuser');

// Check if resume_agent role exists
const roleRes = await client.query("SELECT 1 FROM pg_roles WHERE rolname = 'resume_agent'");
if (roleRes.rows.length === 0) {
  console.log('Creating role resume_agent...');
  await client.query("CREATE ROLE resume_agent WITH LOGIN CREATEDB PASSWORD 'resume_agent_secret'");
} else {
  console.log('Updating password for role resume_agent...');
  await client.query("ALTER ROLE resume_agent WITH LOGIN CREATEDB PASSWORD 'resume_agent_secret'");
}

// Check if resume_agent database exists
const dbRes = await client.query("SELECT 1 FROM pg_database WHERE datname = 'resume_agent'");
if (dbRes.rows.length === 0) {
  console.log('Creating database resume_agent...');
  await client.query("CREATE DATABASE resume_agent OWNER resume_agent");
}

console.log('Done ensuring resume_agent user and database exist!');
await client.end();

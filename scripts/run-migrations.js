const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function findPython() {
  const commands = ['python3'];
  for (const cmd of commands) {
    try {
      execSync(`command -v ${cmd}`, { stdio: 'ignore' });
      return cmd;
    } catch (e) {
      continue;
    }
  }
  throw new Error('python3 not found. Please install python3.');
}

function ensureVenv() {
  const venvPath = path.join(process.cwd(), 'venv');
  const pythonCmd = findPython();
  
  if (!fs.existsSync(venvPath)) {
    console.log('Creating virtual environment...');
    try {
      execSync(`${pythonCmd} -m venv venv`, { stdio: 'inherit' });
      console.log('Virtual environment created!');
    } catch (error) {
      console.error('Failed to create virtual environment:', error.message);
      console.error('Please install python3-venv: apt install python3-venv');
      process.exit(1);
    }
  }
  
  const venvPython = path.join(venvPath, 'bin', 'python');
  if (!fs.existsSync(venvPython)) {
    console.error('Virtual environment Python not found!');
    process.exit(1);
  }
  
  return venvPython;
}

function installRequirements(venvPython) {
  const requirementsPath = path.join(process.cwd(), 'requirements.txt');
  if (fs.existsSync(requirementsPath)) {
    console.log('Installing Python requirements...');
    try {
      execSync(`${venvPython} -m pip install -q -r requirements.txt`, { 
        stdio: 'inherit' 
      });
    } catch (error) {
      console.warn('Warning: Failed to install requirements:', error.message);
    }
  }
}

console.log('Running Alembic migrations...');

try {
  const venvPython = ensureVenv();
  installRequirements(venvPython);
  
  console.log('Running migrations...');
  execSync(`${venvPython} -m alembic upgrade head`, { 
    stdio: 'inherit',
    env: { ...process.env },
    cwd: process.cwd()
  });
  console.log('Migrations completed successfully!');
} catch (error) {
  if (error.status === 0) {
    console.log('Migrations completed!');
  } else {
    console.error('Migration failed:', error.message);
    process.exit(1);
  }
}



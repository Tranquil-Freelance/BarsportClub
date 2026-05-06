import { spawn } from 'child_process';
import { NextResponse } from 'next/server';
import path from 'path';

export async function POST() {
    try {
        // process.cwd() = frontend/ → risali di un livello per puntare alla root del progetto
        const projectRoot = path.resolve(process.cwd(), '..');
        const scriptPath = path.join(projectRoot, 'backend', 'scraping_definitivo');

        const scraperProcess = spawn('python3', [scriptPath], {
            detached: true,
            stdio: 'ignore',
        });

        scraperProcess.unref(); // Sgancia il processo – non blocca l'API

        return NextResponse.json(
            { status: 'success', message: 'Motore di scraping avviato in background' },
            { status: 200 }
        );
    } catch (error) {
        console.error('Errore avvio scraper:', error);
        return NextResponse.json(
            { status: 'error', message: 'Impossibile avviare lo script' },
            { status: 500 }
        );
    }
}

from worker.loader import app, storage
from worker.schemas import requests
from pathlib import Path
from collections import defaultdict
from fastapi import UploadFile, File, Form
from worker.utils.hashcat import HashcatRunner

import asyncio
import shutil
import os
import time

@app.get("/")
async def main():
    return {'status': 'ok'}

@app.post("/install-rule")
async def ruleInstall(
    rule: UploadFile = File(...),
    dest: str = Form("~/worker/rules/")
):
    expanded_path = os.path.expanduser(dest)
    Path(expanded_path).mkdir(parents=True, exist_ok=True)

    try:
        target_path = Path(expanded_path) / rule.filename

        with target_path.open("wb") as buffer:
            shutil.copyfileobj(rule.file, buffer)

        storage.insert('rules', {'filename': rule.filename, 'file_path': str(target_path)})
    except Exception as ex:
        return {"status": "error", "error": str(ex)}

    return {"status": "ok", "saved_to": str(target_path)}

@app.post("/install-base")
async def baseInstall(
    base: UploadFile = File(...),
    dest: str = Form("~/worker/bases/")
):
    expanded_path = os.path.expanduser(dest)
    Path(expanded_path).mkdir(parents=True, exist_ok=True)

    try:
        target_path = Path(expanded_path) / base.filename

        with target_path.open("wb") as buffer:
            shutil.copyfileobj(base.file, buffer)

        storage.insert('bases', {'filename': base.filename, 'file_path': str(target_path)})
    except Exception as ex:
        return {"status": "error", "error": str(ex)}

    return {"status": "ok", "saved_to": str(target_path)}

@app.post('/install-hash')
async def installHash(request: requests.InstallHash):
    try:
        expanded_path = Path(os.path.expanduser(request.dest))
        expanded_path.mkdir(parents=True, exist_ok=True)

        target_path = expanded_path / f"{request.id}.txt"

        data = request.hash.encode()

        with target_path.open("wb") as buffer:
            buffer.write(data)

        storage.insert('hashes', {
            'filename': target_path.name,
            'file_path': str(target_path),
            'hash': request.hash,
            'hash_type': request.hash_type
        })

        for rule in storage.all('rules'):
            for base in storage.all('bases'):
                rule_path = rule.get('file_path')
                base = base.get('file_path')
                if rule_path:
                    storage.insert('hashqueue', {
                        'id': request.id,
                        'hash': request.hash,
                        'hash_type': request.hash_type,
                        'rule': rule_path,
                        'base': base,
                        'status': 'waiting'
                    })

        return {"status": "ok", "saved_to": str(target_path)}

    except Exception as ex:
        return {"status": "error", "error": str(ex)}

@app.get('/hash-in-work')
async def hashInWork():
    response = {
        'servertime': time.time(),
        'status': 'ok',
        'hashes': defaultdict(dict),
    }

    try:
        all_results = storage.all('result')

        for res in all_results:
            id = res.get('id')
            hash = res.get('hash')
            hash_path = res.get('hash_path')
            result = res.get('result')

            response['hashes'][id] = {
                'hash': hash,
                'hash_path': hash_path,
                'result': result
            }

    except Exception as ex:
        response['status'] = 'error'
        response['error'] = str(ex)

    return response

@app.get('/getUploadedBases')
async def hashInWork():
    response = {
        'servertime': time.time(),
        'status': 'ok',
        'bases': defaultdict(dict),
    }

    try:
        all_results = storage.all('bases')

        for res in all_results:
            id = res.get('file_name')
            file_path = res.get('file_path')

            response['bases'][id] = {
                'file_path': file_path,
            }

    except Exception as ex:
        response['status'] = 'error'
        response['error'] = str(ex)

    return response

@app.get('/getUploadedRules')
async def hashInWork():
    response = {
        'servertime': time.time(),
        'status': 'ok',
        'rules': defaultdict(dict),
    }

    try:
        all_results = storage.all('rules')

        for res in all_results:
            id = res.get('file_name')
            file_path = res.get('file_path')

            response['rules'][id] = {
                'file_path': file_path,
            }

    except Exception as ex:
        response['status'] = 'error'
        response['error'] = str(ex)

    return response

@app.post('/reInstallbases')
async def hashInWork():
    response = {
        'servertime': time.time(),
        'status': 'ok',
        'bases': defaultdict(dict),
    }

    try:
        all_results = storage.all('bases')

        for res in all_results:
            id = res.get('file_name')
            file_path = res.get('file_path')

            response['bases'][id] = {
                'file_path': file_path,
            }

        storage.delall('bases')

        base_dir = "/worker/bases"
        if os.path.exists(base_dir):
            for file in os.listdir(base_dir):
                file_path = os.path.join(base_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)

    except Exception as ex:
        response['status'] = 'error'
        response['error'] = str(ex)

    return response

@app.post('/reInstallrules')
async def hashInWork():
    response = {
        'servertime': time.time(),
        'status': 'ok',
        'rules': defaultdict(dict),
    }

    try:
        all_results = storage.all('rules')

        for res in all_results:
            id = res.get('file_name')
            file_path = res.get('file_path')

            response['rules'][id] = {
                'file_path': file_path,
            }

        storage.delall('rules')

        base_dir = "/worker/rules"
        if os.path.exists(base_dir):
            for file in os.listdir(base_dir):
                file_path = os.path.join(base_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)

    except Exception as ex:
        response['status'] = 'error'
        response['error'] = str(ex)

    return response

MAX_GPUS = 8

async def run_task_on_gpu(task, gpu_id):
    runner = HashcatRunner()
    try:
        hash_path = Path(f"/tmp/{task['id']}.hash")
        hash_path.write_text(task["hash"])

        output_path = Path(f"/worker/{task['id']}.txt")
        storage.update('hashqueue', {'status': 'inproccess'}, id=task['id'], rule=task.get('rule'), base=task.get('base'))

        extra_args = [
            '--opencl-device-types=2',
            f'--gpu-devices={gpu_id}'
        ]

        runner.start_bruteforce(
            hash_file=str(hash_path),
            dict_file=task.get('base'),
            rule_file=task.get('rule'),
            output_file=str(output_path),
            hash_type=task.get("hash_type", 28200),
            id=task["id"],
            extra_args=extra_args
        )

        while runner.is_running():
            await asyncio.sleep(1)

        status = runner.get_status()
        output_file = Path(status.get('output_file'))
        storage.delete('hashqueue', id=runner.id, status='inproccess')

        if output_file.exists():
            storage.insert('result', {
                'id': runner.id,
                'hash': output_file.read_text().strip(),
                'hash_path': str(output_file),
                'result': True
            })
            storage.delall('hashqueue')
        
        runner.reset()
    except Exception as e:
        print(f"Error on GPU {gpu_id} for task {task['id']}: {e}")

async def process_hashqueue():
    while True:
        queue = [task for task in storage.all("hashqueue") if task.get("status") == "waiting"]
        print(f"Queue length: {len(queue)}")
        if not queue:
            await asyncio.sleep(5)
            continue

        batch = queue[:MAX_GPUS]

        tasks = []
        for gpu_id, task in enumerate(batch):
            tasks.append(run_task_on_gpu(task, gpu_id))

        await asyncio.gather(*tasks)

        await asyncio.sleep(1)

@app.on_event("startup")
async def start_background_worker():
    asyncio.create_task(process_hashqueue())

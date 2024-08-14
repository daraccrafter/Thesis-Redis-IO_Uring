import asyncio
import redis.asyncio as redis
import subprocess
import signal
import time
import random
import argparse


def start_redis_server(port, cwd):
    command = [
        "./src/redis-server",
        "redis.conf",
        "--port",
        str(port),
    ]
    process = subprocess.Popen(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    for line in iter(process.stdout.readline, ""):
        if "Ready to accept connections" in line:
            return process


def stop_redis_server(process):
    if process:
        process.send_signal(signal.SIGTERM)
        process.wait()
        time.sleep(3)


async def monitor_redis_logs(process, start_time):
    """Monitor the Redis server logs for 'Final fsync completed'."""
    for line in iter(process.stdout.readline, ""):
        decoded_output = line.strip()
        if "Final fsync completed" in decoded_output:
            end_time = time.time()
            print(
                f"Final fsync completed detected. Time taken: {end_time - start_time} seconds"
            )
            return end_time


async def set_diffkeys(redis_client, start_key, end_key, value_prefix="value"):
    bgrewriteaof_triggered = False
    random_trigger_point = random.randint(start_key, end_key)

    for i in range(start_key, end_key + 1):
        key = f"key_{i}"
        try:
            value = f"{value_prefix}_{i}"
            await redis_client.set(key, value)
            if not bgrewriteaof_triggered and i == random_trigger_point:
                print(f"\tTriggering random BGREWRITEAOF after {i} requests")
                await redis_client.bgrewriteaof()
                bgrewriteaof_triggered = True

            if i % 10000 == 0:
                print(f"\tSET command executed {i} times")
        except Exception as e:
            print(f"\tFailed to set key {key}: {e}")


async def set_incr_commands(redis_client, start_key, end_key):
    bgrewriteaof_triggered = False
    random_trigger_point = random.randint(start_key, end_key)

    for i in range(start_key, end_key + 1):
        key = "incr_key"
        try:
            await redis_client.incr(key)
            if not bgrewriteaof_triggered and i == random_trigger_point:
                print(f"\tTriggering random BGREWRITEAOF after {i} requests")
                await redis_client.bgrewriteaof()
                bgrewriteaof_triggered = True

            if i % 10000 == 0:
                print(f"\tINCR command executed {i} times")
        except Exception as e:
            print(f"\tFailed to execute INCR for key {key}: {e}")


async def set_samekey_diffvalue(redis_client, start_key, end_key):
    bgrewriteaof_triggered = False
    random_trigger_point = random.randint(start_key, end_key)

    for i in range(start_key, end_key + 1):
        key = f"key"
        try:
            await redis_client.set(key, i)
            if not bgrewriteaof_triggered and i == random_trigger_point:
                print(f"\tTriggering random BGREWRITEAOF after {i} requests")
                await redis_client.bgrewriteaof()
                bgrewriteaof_triggered = True

            if i % 10000 == 0:
                print(f"\tSET command executed {i} times")
        except Exception as e:
            print(f"\tFailed to execute SET for key {key}, value {i}: {e}")


async def verify_keys(redis_client, start_key, end_key, expected_value_prefix="value"):
    success = True
    logs = []
    for i in range(start_key, end_key + 1):
        key = f"key_{i}"
        try:
            expected_value = f"{expected_value_prefix}_{i}"
            value = await redis_client.get(key)
            if value is None:
                log = f"{key},{expected_value},MISSING"
                print(f"Key {key} is missing!")
                success = False
            elif value.decode() != expected_value:
                log = f"{key},{expected_value},{value.decode()}"
                print(
                    f"Key {key} has incorrect value: {value.decode()} (expected: {expected_value})"
                )
                success = False
            else:
                log = f"{key},{expected_value},{value.decode()}"
            logs.append(log)
        except Exception as e:
            log = f"{key},{expected_value},ERROR:{e}"
            print(f"Failed to verify key {key}: {e}")
            success = False
            logs.append(log)

    with open("verify_keys_log.csv", "w") as file:
        file.write("Key,Expected Value,Actual Value\n")
        for log in logs:
            file.write(log + "\n")

    if success:
        print(f"Successfully verified keys from {start_key} to {end_key}.")


async def verify_incr(redis_client, expected_value):
    key = "incr_key"
    try:
        value = await redis_client.get(key)
        with open("verify_incr_log.csv", "w") as file:
            file.write("Key,Expected Value,Actual Value\n")
            if value is None:
                file.write(f"{key},{expected_value},MISSING\n")
                print(f"Key {key} is missing!")
            elif int(value) != expected_value:
                file.write(f"{key},{expected_value},{value.decode()}\n")
                print(
                    f"Key {key} has incorrect value: {value.decode()} (expected: {expected_value})"
                )
            else:
                file.write(f"{key},{expected_value},{value.decode()}\n")
                print(f"INCR key verified successfully with value {value.decode()}.")
    except Exception as e:
        print(f"Failed to verify key {key}: {e}")


async def verify_samekey_diffvalue(redis_client, end_key):
    key = "key"
    try:
        value = await redis_client.get(key)
        with open("verify_samekey_log.csv", "w") as file:
            file.write("Key,Expected Value,Actual Value\n")
            if value is None:
                file.write(f"{key},{end_key},MISSING\n")
                print(f"Key {key} is missing!")
            elif int(value) != end_key:
                file.write(f"{key},{end_key},{value.decode()}\n")
                print(
                    f"Key {key} has incorrect value: {value.decode()} (expected: {end_key})"
                )
            else:
                file.write(f"{key},{end_key},{value.decode()}\n")
                print(f"SET key verified successfully with value {value.decode()}.")
    except Exception as e:
        print(f"Failed to verify key {key}: {e}")


async def run_test_suite(requests):
    try:
        subprocess.run(["rm", "-rf", "appendonlydir"], cwd="../redis-io_uring")
        redis_process = start_redis_server(6385, cwd="../redis-io_uring")

        redis_client = redis.from_url("redis://localhost:6385")
        await redis_client.config_set("correct-test", "yes")
        await redis_client.config_set("correct-test-reqnum", requests)

        print("#### Starting Test 1: Setting keys with incrementing names")
        start_time = time.time()
        await set_diffkeys(redis_client, 1, requests)
        end_time = await monitor_redis_logs(redis_process, start_time)

        print(f"\tTime taken: {end_time - start_time} seconds")
        await verify_keys(redis_client, 1, requests)
        stop_redis_server(redis_process)
        redis_process = start_redis_server(6386, cwd="../redis-io_uring")
        redis_client = redis.from_url("redis://localhost:6386")
        await redis_client.config_set("correct-test", "yes")
        await redis_client.config_set("correct-test-reqnum", requests)

        start_time = time.time()
        print("#### Starting Test 2: INCR commands on a single key")
        await set_incr_commands(redis_client, 1, requests)
        end_time = await monitor_redis_logs(redis_process, start_time)

        print(f"\tTime taken: {end_time - start_time} seconds")
        await verify_incr(redis_client, requests)

        stop_redis_server(redis_process)

        redis_process = start_redis_server(6387, cwd="../redis-io_uring")
        redis_client = redis.from_url("redis://localhost:6387")
        await redis_client.config_set("correct-test", "yes")
        await redis_client.config_set("correct-test-reqnum", requests)
        print("#### Starting Test 3: Setting same keys with incrementing values")
        start_time = time.time()
        await set_samekey_diffvalue(redis_client, 1, requests)
        end_time = await monitor_redis_logs(redis_process, start_time)
        print(f"\tTime taken: {end_time - start_time} seconds")
        await verify_samekey_diffvalue(redis_client, requests)

        stop_redis_server(redis_process)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if redis_process:
            stop_redis_server(redis_process)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests.")
    parser.add_argument(
        "--requests", type=int, default=100000, help="Request count for the benchmark."
    )
    args = parser.parse_args()
    asyncio.run(run_test_suite(args.requests))

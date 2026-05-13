import http from 'k6/http';
import { check, sleep } from 'k6';

const baseUrl = __ENV.BASE_URL || 'http://host.docker.internal:8080';
const cpuWork = __ENV.CPU_WORK || '12000';

export const options = {
  vus: Number(__ENV.VUS || 50),
  duration: __ENV.DURATION || '60m',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const r1 = http.get(`${baseUrl}/bench/read`);
  check(r1, { 'read status is 200': (r) => r.status === 200 });

  const r2 = http.get(`${baseUrl}/bench/cpu?work=${cpuWork}`);
  check(r2, { 'cpu status is 200': (r) => r.status === 200 });

  if (__ITER % 10 === 0) {
    const r3 = http.get(`${baseUrl}/hello`);
    check(r3, { 'hello status is 200': (r) => r.status === 200 });
  }

  sleep(0.1);
}


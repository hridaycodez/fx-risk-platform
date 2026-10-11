const request = require('supertest');
const app = require('../app');

describe('GET /health', () => {
  it('should return 200 and healthy status', async () => {
    const res = await request(app).get('/health');
    expect(res.statusCode).toEqual(200);
    expect(res.body).toHaveProperty('status', 'ok');
    expect(res.body).toHaveProperty('service');
  });
});

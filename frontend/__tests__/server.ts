/// <reference types="vitest/globals" />
import MockAdapter from "axios-mock-adapter";
import { api } from "../src/api/axios";

export const mock = new MockAdapter(api);
afterEach(() => mock.reset());

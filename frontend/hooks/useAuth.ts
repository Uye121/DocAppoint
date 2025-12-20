import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { login, signup, verifyEmail, resendVerify } from "../api/auth";
import { LoginPayload, SignupPayload } from "../types/auth";
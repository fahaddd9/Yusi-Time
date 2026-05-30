import { z } from "zod"

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
})

export const signupSchema = z.object({
  full_name: z.string().min(1, "Name is required").max(100).trim(),
  email: z.string().email("Enter a valid email address").max(254),
  password: z.string().min(8, "Minimum 8 characters"),
})

export const forgotPasswordSchema = z.object({
  email: z.string().email("Enter a valid email address"),
})

export const resetPasswordSchema = z
  .object({
    new_password: z.string().min(8, "Minimum 8 characters"),
    confirm_password: z.string(),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Passwords don't match",
    path: ["confirm_password"],
  })

export type LoginInput = z.infer<typeof loginSchema>
export type SignupInput = z.infer<typeof signupSchema>
export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>
export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>

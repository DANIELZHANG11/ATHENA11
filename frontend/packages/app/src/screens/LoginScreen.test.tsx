import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom";
import { LoginScreen } from "./LoginScreen";
import { TamaguiProvider } from "@athena/ui";

// Mock i18n
vi.mock("../i18n", () => ({
  t: (key: string, params?: any) => {
    if (key === "auth.email_placeholder") return "auth.email_placeholder";
    if (key === "auth.get_code") return "Get Code";
    if (key === "auth.confirm_email_title") return "Confirm Email Address";
    if (key === "auth.confirm_email_message")
      return "We will send a verification code to this email. Please confirm it's correct.";
    if (key === "auth.confirm_send") return "Confirm Send";
    if (key === "auth.verification_code") return "Verification Code";
    if (key === "auth.login_register") return "Login/Register";
    if (params && params.seconds) return `Resend (${params.seconds}s)`;
    return key;
  },
}));

// Mock TamaguiProvider to avoid complex setup if possible,
// but using the real one is better if it works.
// However, the real TamaguiProvider might depend on fonts or other native things.
// Let's try to use a simple wrapper that provides the theme context.
// Since LoginScreen uses useTheme(), we need a provider.
// If @athena/ui TamaguiProvider fails, we can mock useTheme.

// Mock tamagui useTheme if needed
// vi.mock('tamagui', async () => {
//   const actual = await vi.importActual('tamagui')
//   return {
//     ...actual,
//     useTheme: () => ({ systemGray: { val: '#ccc' }, systemBlue: { val: 'blue' }, label: { val: 'black' } }),
//   }
// })

// Let's rely on TamaguiProvider first.

describe("LoginScreen", () => {
  it("renders email input and OAuth buttons", () => {
    render(
      <TamaguiProvider>
        <LoginScreen />
      </TamaguiProvider>,
    );

    expect(
      screen.getByPlaceholderText("auth.email_placeholder"),
    ).toBeInTheDocument();
    expect(screen.getByText("Get Code")).toBeInTheDocument();

    // Check for OAuth buttons
    expect(screen.getByText("auth.login_with_wechat")).toBeInTheDocument();
    expect(screen.getByText("auth.login_with_google")).toBeInTheDocument();
    expect(screen.getByText("auth.login_with_microsoft")).toBeInTheDocument();
    expect(screen.getByText("auth.login_with_apple")).toBeInTheDocument();
  });

  it("shows confirmation dialog when clicking Get Code", async () => {
    render(
      <TamaguiProvider>
        <LoginScreen />
      </TamaguiProvider>,
    );

    const emailInput = screen.getByPlaceholderText("auth.email_placeholder");
    const getCodeBtn = screen.getByText("Get Code");

    // Enter email
    fireEvent.change(emailInput, { target: { value: "test@example.com" } });

    // Click Get Code
    fireEvent.click(getCodeBtn);

    // Check confirmation dialog
    expect(screen.getByText("Confirm Email Address")).toBeInTheDocument();
    expect(screen.getByText("test@example.com")).toBeInTheDocument();
  });

  it("switches to verification code input after confirmation", async () => {
    render(
      <TamaguiProvider>
        <LoginScreen />
      </TamaguiProvider>,
    );

    const emailInput = screen.getByPlaceholderText("auth.email_placeholder");
    const getCodeBtn = screen.getByText("Get Code");

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.click(getCodeBtn);

    // Click Confirm Send in dialog
    const confirmSendBtn = screen.getByText("Confirm Send");
    fireEvent.click(confirmSendBtn);

    // Should see verification code input
    await waitFor(() => {
      expect(screen.getByPlaceholderText("000000")).toBeInTheDocument();
    });
  });
});

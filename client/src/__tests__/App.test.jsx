/**
 * Basic smoke tests for the App component.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import App from "../App";

// Wrap component with router since App uses react-router
const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("App", () => {
  it("renders without crashing", () => {
    // Basic smoke test - app should render without throwing
    expect(() => renderWithRouter(<App />)).not.toThrow();
  });
});




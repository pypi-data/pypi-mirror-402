/**
 * TypeScript definitions for qwed-ucp
 */

export interface VerificationResult {
    verified: boolean;
    guardsPassed: number;
    guardsFailed: number;
    details: GuardResult[];
    error: string | null;
}

export interface GuardResult {
    guard: string;
    verified: boolean;
    error: string | null;
}

export interface MiddlewareOptions {
    /** Paths to verify (default: ['/checkout', '/checkout-sessions', '/payment', '/cart']) */
    verifyPaths?: string[];
    /** HTTP methods to verify (default: ['POST', 'PUT', 'PATCH']) */
    verifyMethods?: string[];
    /** Block request on verification failure (default: true) */
    blockOnFailure?: boolean;
    /** Callback when verification succeeds */
    onVerified?: (result: VerificationResult, req: any) => void;
    /** Callback when verification fails */
    onFailed?: (result: VerificationResult, req: any) => void;
}

export interface Checkout {
    currency?: string;
    status?: string;
    totals?: Total[];
    line_items?: LineItem[];
    order?: any;
}

export interface Total {
    type: 'subtotal' | 'tax' | 'discount' | 'fulfillment' | 'fee' | 'total';
    amount: number;
}

export interface LineItem {
    id: string;
    quantity?: number;
    price?: number;
    item?: {
        price?: number;
    };
}

/**
 * Create Express.js middleware for QWED-UCP verification
 */
export function createQWEDUCPMiddleware(options?: MiddlewareOptions): (req: any, res: any, next: any) => void;

/**
 * Verify a checkout object locally
 */
export function verifyCheckoutLocally(checkout: Checkout): VerificationResult;

/**
 * Verify currency is valid ISO 4217
 */
export function verifyCurrency(checkout: Checkout): { verified: boolean; error: string | null };

/**
 * Verify totals add up correctly
 */
export function verifyTotalsMath(checkout: Checkout): { verified: boolean; error: string | null };

/**
 * Verify checkout state is valid
 */
export function verifyState(checkout: Checkout): { verified: boolean; error: string | null };

/**
 * Verify line items calculate correctly
 */
export function verifyLineItems(checkout: Checkout): { verified: boolean; error: string | null };

/**
 * Alias for createQWEDUCPMiddleware
 */
export const middleware: typeof createQWEDUCPMiddleware;

/**
 * Alias for verifyCheckoutLocally
 */
export const verify: typeof verifyCheckoutLocally;

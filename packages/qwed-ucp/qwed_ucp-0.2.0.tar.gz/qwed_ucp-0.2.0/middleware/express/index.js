/**
 * QWED-UCP - Verification Guards for Universal Commerce Protocol
 * 
 * Catch AI math errors in commerce transactions before payment.
 * 
 * @example
 * const { createQWEDUCPMiddleware } = require('qwed-ucp');
 * app.use(createQWEDUCPMiddleware());
 */

const {
    createQWEDUCPMiddleware,
    verifyCheckoutLocally,
    verifyCurrency,
    verifyTotalsMath,
    verifyState,
    verifyLineItems
} = require('./qwed-ucp-middleware');

module.exports = {
    // Main middleware factory
    createQWEDUCPMiddleware,

    // Verify a checkout object
    verifyCheckoutLocally,

    // Individual guards
    verifyCurrency,
    verifyTotalsMath,
    verifyState,
    verifyLineItems,

    // Convenience aliases
    middleware: createQWEDUCPMiddleware,
    verify: verifyCheckoutLocally
};

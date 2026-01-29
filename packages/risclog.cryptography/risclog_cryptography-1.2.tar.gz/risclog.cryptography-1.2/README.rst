====================
risclog.cryptography
====================

.. image:: https://github.com/risclog-solution/risclog.cryptography/actions/workflows/test.yml/badge.svg
     :target: https://github.com/risclog-solution/risclog.cryptography/actions/workflows/test.yml
     :alt: CI Status


.. image:: https://img.shields.io/pypi/v/risclog.cryptography.svg
        :target: https://pypi.python.org/pypi/risclog.cryptography


The CryptographyManager is a tool designed to securely encrypt and decrypt messages and data. It uses modern encryption techniques to protect confidential information.


* Free software: MIT license
* Documentation: https://pypi.org/project/risclog.cryptography.


Requirements
============

To use the CryptographyManager, ensure you have the following:
    * Python 3.9 or later
    * The cryptography library, which can be installed using pip install cryptography.


Installation
============

Download the code for the CryptographyManager into your Python environment or add it directly to your Python project. Make sure that all dependencies are installed.

Example for installing the cryptography library::

   $ pip install risclog.cryptography


Usage
=====

Initialization
--------------

To use the CryptographyManager, you will need a password and a "salt" (a random string to enhance security).

.. code-block:: python

   from risclog.cryptography import CryptographyManager

   password = "my_secure_password"
   salt = "my_secure_salt"

   # Initialize the CryptographyManager
   crypto_manager = CryptographyManager(password=password, salt=salt)

Encryption
----------

To encrypt a message, use the encrypt method. This is particularly useful for protecting sensitive data like passwords or personal information.

#. Input the text you want to encrypt.
#. Call the encrypt method.


.. code-block:: python

   message = "This is a secret message"
   encrypted_message = crypto_manager.encrypt(message)

   print(f"Encrypted message: {encrypted_message}")

Decryption
----------

To decrypt an encrypted message, use the decrypt method:

#. Call the decrypt method with the encrypted message.
#. The original message will be restored.

.. code-block:: python

   decrypted_message = crypto_manager.decrypt(encrypted_message)

   print(f"Decrypted message: {decrypted_message}")


Troubleshooting
===============

**Wrong password or salt:** If you try to decrypt a message with a different password or salt than what was used for encryption, you will get an error. Make sure to use the same password and salt.

**Invalid messages:** Encryption requires valid strings or bytes. Ensure the text is correctly formatted.

**Event-loop issues (with async):** If you're using the encryption in an asynchronous environment (e.g., web applications), the manager will automatically detect if an event loop is running and adjust accordingly.

Security Tips
=============

**Password security:** Choose a strong and secure password. A weak password can compromise the security of the encryption.

**Use salt:** Whenever possible, use a salt to make brute-force attacks more difficult. The salt should be unique for each user or message.

**Key storage:** Safeguard the password and salt securely. If they are lost, encrypted data cannot be recovered.

Tests
=====

Run tests::

    $ ./pytest


Credits
=======

This package was created with Cookiecutter_ and the `risclog-solution/risclog-cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`risclog-solution/risclog-cookiecutter-pypackage`: https://github.com/risclog-solution/risclog-cookiecutter-pypackage


This package uses AppEnv_ for running tests inside this package.

.. _AppEnv: https://github.com/flyingcircusio/appenv

Safe Delegation
===============


Safe delegation, as provided by Zope and Allaire's Spectra, is not
implemented in Cheetah. The core aim has been to help developers
and template maintainers get things done, without throwing
unnecessary complications in their way. So you should give write
access to your templates only to those whom you trust. However,
several hooks have been built into Cheetah so that safe delegation
can be implemented at a later date.

It should be possible to implement safe delegation via a future
configuration Setting {safeDelegationLevel} (0=none, 1=semi-secure,
2-alcatraz). This is not implemented but the steps are listed here
in case somebody wants to try them out and test them.

Of course, you would also need to benchmark your code and verify it
does not impact performance when safe delegation is off, and
impacts it only modestly when it is on." All necessary changes can
be made at compile time, so there should be no performance impact
when filling the same TO multiple times.


#. Only give untrusted developers access to the .tmpl files.
   (Verifying what this means. Why can't trusted developers access
   them?)

#. Disable the {#attr} directive and maybe the {#set} directive.

#. Use Cheetah's directive validation hooks to disallow references
   to {self}, etc (e.g. {#if $steal(self.thePrivateVar)} )

#. Implement a validator for the $placeholders and use it to
   disallow '\_\_' in $placeholders so that tricks like
   {$obj.\_\_class\_\_.\_\_dict\_\_} are not possible.




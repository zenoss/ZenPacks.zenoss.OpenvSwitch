Follow these instructions to load this ZenPack's Analytics resources.

1. Login to Analytics with Internal Authentication as superuser.

2. Verify that the repository path "/root/Public/OpenvSwitch ZenPack" doesn't
   already exist. If it does, move this folder elsewhere in the Analytics
   repository or remove it altogether before proceeding.

3. Navigate to Manage->Server Settings->Import and browse to the
   analytics-bundle.zip file included in the ZenPack.

4. Uncheck ALL Import options. It is absolutely critical to make sure "Update"
   is NOT checked.

5. Click "Import" button. The zip file import should report a success flare.
   Click "close" on the flare.

6. Navigate to "/root/Public/OpenvSwitch ZenPack" in the Analytics repository
   and verify the the folder was successfully created.

7. Log out and login as a regular Zenoss Analytics user and verify that you
   can use the Domains and Views under the "Public/OpenvSwitch ZenPack" folder.

import aiohttp
from aioshock.exceptions import ApiException
from aioshock.enums import UserLookupType, BanLookupType
from urllib.parse import urljoin, urlencode

class TShock():
    """The main API wrapper. This class handles all async requests.
    The functions in this class document what endpoint they belong to
    and have names that describe their functions.
    \n
    All of the functions beginning with ``fetch_`` do not edit any server values.
    ``fetch_`` functions simply query the TShock server using any of the REST endpoints
    that do not update, create, or delete data. An example is returning a list of players.
    Of CRUD, ``fetch_`` covers Read.
    \n
    All of the functions beginning with ``set_`` will edit some sort of value on the server's end.
    ``set_`` functions are used to update, create, or delete data. An example is banning a player.
    Of CRUD, ``set_`` covers Update.
    \n
    All of the functions beginning with ``do_`` will perform some sort of action that
    will edit the TShock server's state somehow, but will not cause permanent changes.
    These are typically actions taken somehow. An example is butchering all NPCs.
    Of CRUD, ``do_`` covers Create and Delete.
    \n
    All of the functions will return a dict. The dict is a mapping of the JSON data
    returned by the TShock server as a REST response. Every response will contain the
    ``status`` member. The ``status`` member is the HTTP status code that the TShock server
    returned. Any statuses other than 200 and 400 will not be returned and will instead
    be thrown as ApiExceptions. Most of the mappings returned will have a ``response``
    member. This indicates success or failure and the best way to find out what
    the mapping will contain would be to consult the REST API source or documentation.
    \n
    After instantiation, the :py:meth:`fetch_token` function should be run to obtain a token
    corresponding to a specific user. All requests will pass the token. You cannot
    make most requests without a token.
    \n
    Your user is required to have the appropriate permission assigned to them by the TShock
    server for some requests. These permissions are not documented here and may be found in the
    TShock RESTful API documenation:
    https://tshock.atlassian.net/wiki/display/TSHOCKPLUGINS/REST+API+Endpoints#RESTAPIEndpoints-/v2/users/activelist
    \n
    Example usage of the API:
    \n
    >>> aioshock = aioshock.TShock()
    >>> await aioshock.fetch_token("Dr-Insanity","test")
    >>> await aioshock.fetch_active_user_list()
    {'status': '200', 'activeusers': 'Dr-Insanity'}
    \n
    ip `str`
    - the ip address of the TShock server
    \n
    port `int`
    - the port that the REST API is opened on
    """
    def __init__(self, ip, port):
        self.urls = RequestBuilder(ip, port)
        self.ip = ip
        self.port = port
        self.token = ""

    async def _make_request(self, url : str) -> dict:
        """Makes a GET request to the specified url.
        Takes care of checking the response status as well
        as handling all possible connection errors.

        :param str url:
            Url string to make a GET request to.

        :returns:
            A dict mapping of the json reply.
            every response dict has a ``status`` member
            indicating the HTTP response status. MOst mappings
            have a ``response`` member.

        :raises ApiException:
            If the request times out or the REST response returns a status other than 200 or 400.
        """
        HEADERS = {
            'User-Agent' : "Pandora's Guard"
        }
        json_outp = []
        async with aiohttp.request("GET", url, headers=HEADERS) as response:
            if response.status == 200:
                results = await response.json()
                #print(results)
                text_data = await response.text()
                #print(text_data)
                json_outp.append(results)

            elif response.status == 404:
                raise ApiException("404 Error. Are you sure the server has REST enabled?")
            elif response.status == 403:

                raise ApiException("403 Error. Was the token and/or user details changed?")
            elif response.status in [200, 400]:
                pass
            else:
                raise ApiException("Error in request. Server returned status: {0} With error: {1}".format(
                    response.status,
                    json_outp[0]["error"]
            ))
            data = json_outp[0]
            return data

    async def fetch_token(self, user : str, password : str):
        """Gets and stores a token for the user.
        The token is used for all rest endpoints that require authentication.
        The token may be overridden by running this function again.

        :param str user:
            String representing the user to obtain the token under.

        :param str password:
            String that is the user's password.

        **endpoint:** v2/token/create/
        """
        url = self.urls.get_url("v2", "token", "create", username=user, password=password)
        data = await self._make_request(url)
        data = data["token"]
        self.urls.token = data

    async def fetch_status(self) -> dict:
        """Gets the server status.

        :returns:
            A dict with these items:
                * name - Server name
                * port - Server port
                * playercount - Amount of players on the server
                * players - CSV list of players currently connected

        **endpoint:** /status
        """
        data = await self._make_request(self.urls.get_url("status"))
        return data

    async def fetch_token_status(self) -> bool:
        """Tests if the the currently saved token is still valid.

        :returns:
            True if the token is valid. False otherwise.

        **endpoint:** /tokentest
        """
        try:
            data = await self._make_request(self.urls.get_url("tokentest"))
            return True
        except ApiException:
            return False

    async def fetch_server_status_v2(self, players=False, rules=False, filters=None) -> dict:
        """Gets the server status. Includes various items based
        on the parameters sent.

        :param bool players:
            Bool deciding if players should be included in the response.

        :param bool rules:
            Bool deciding if server config rules should be included in the response.

        :param dict filters:
            Dict of filters to be applied to the player search. May contain these items:
                * nickname
                * username
                * group
                * active
                * state
                * team

        :returns:
            A dict with these items:
                * name - Server name
                * port - Port the server is running on
                * playercount - Number of players currently online
                * maxplayers - The maximum number of players the server support
                * world - The name of the currently running world
                * players - (optional) an array of players including the following information:
                    * nickname
                    * username
                    * ip
                    * group
                    * active
                    * state
                    * team
                * rules - (optional) an array of server rules which are name value pairs e.g. AutoSave, DisableBuild etc

        **endpoint:** /v2/server/status
        """
        if filters is None:
            filters = {}
        data = await self._make_request(self.urls.get_url("v2", "server", "status", players=players, rules=rules, **filters))
        return data

    async def fetch_active_user_list(self):
        """Gets the currently active players logged into a server.

        :returns:
            A dict with these items:
                * activeusers - list of active users

        **endpoint:** /v2/users/activelist
        """
        data = await self._make_request(self.urls.get_url("v2", "users", "activelist"))
        return data
    async def fetch_user_info(self, lookup : UserLookupType, user : str):
        """Gets information about a specific user.

        :param UserLookupType lookup:
            Should be a value of the UserLookupType Enum stating what the
            lookup value is.

        :param str user:
            String that is either the user name, id, or ip, depending on the
            lookup type.

        :returns:
            A dict with these items:
                * group - The group the user belong's to
                * id - The user's ID
                * name - The name of the user
                * ip - The ip of the user

        **endpoint:** /v2/users/read
        """
        data = await self._make_request(self.urls.get_url("v2", "users", "read", type=lookup.value, user=user))
        return data

    async def set_group(self, user: str, newgroup: str):
        """Sets the group for specific user.

        ## user
        - The username of the user to change the group for

        ## returns:
        - Dict
        """
        data = await self.do_server_rawcmd(f"/user group {user} {newgroup}")
        return data

    async def fetch_ban_information(self, lookup : BanLookupType, user : str) -> dict:
        """Gets information about a ban.

        :param BanLookupType lookup:
            a BanLookupType value dictating how to search
            for the user

        :param str user:
            the user info to search for

        :returns:
            a dict with these items:
                * name - The username of the player
                * ip - The IP address of the player
                * reason - The reason the player was banned

        **endpoint:** /v2/bans/read
        """
        data = await self._make_request(self.urls.get_url("v2", "bans", "read", type=lookup.value, ban=user))
        return data

    async def fetch_ban_list(self):
        """Gets a list of all of the bans on the server.

        :returns:
            A dict with these items:
                * bans - An array of all the currently banned players including:
                    * name
                    * ip
                    * reason

        **endpoint:** /v2/bans/list
        """
        data = await self._make_request(self.urls.get_url("v2", "bans", "list"))
        return data

    async def fetch_player_list(self):
        """Gets a list of all of the players currently on the server.

        :returns:
            A dict with these items:
                * players - A list of all current players on the server, separated by a comma.

        **endpoint:** /v2/players/list
        """
        data = await self._make_request(self.urls.get_url("v2", "players", "list"))
        return data
    
    async def fetch_player_info(self, player : str):
        """Gets information about a specific player.
        :param str player:
            The player to look for, by name.
        :returns:
            A dict with these items:
                * nickname - The player's nickname
                * username - The player's username (if they are registered)
                * ip - The player's IP address
                * group - The group that the player belongs to
                * register - time whene he register
                * position - The player's current position on the map
                * inventory - A list of all items in the player's inventory
                * armor - his armor
                * dyes - player`s item in dyes slot
                * buffs - A list of all buffs that are currently affecting the player
        **endpoint:** /v2/players/read
        """
        data = await self._make_request(self.urls.get_url("players", "read", player=player))
        return data
    
    async def fetch_player_info_v4(self, player : str):
        """Gets information about a specific player.

        :param str player:
            The player to look for, by name.

        :returns:
            A dict with these items:
                * nickname - The player's nickname
                * username - The player's username (if they are registered)
                * ip - The player's IP address
                * group - The group that the player belongs to
                * register - time whene he register
                * muted - if player muted
                * position - The player's current position on the map
                * inventory - A list of all items in the player's inventory
                * item - player`s item
                    * inventory - player`s item in inventory
                    * equipment - player`s equipment
                    * dyes - player`s item in dyes slot
                    * piggy - player`s item in piggy
                    * safe -  player`s item in safe
                    * forge - player`s item in forge 
                * buffs - A list of all buffs that are currently affecting the player

        **endpoint:** /v4/players/read
        """
        data = await self._make_request(self.urls.get_url("v4", "players", "read", player=player))
        return data

    async def fetch_world_info(self):
        """Gets some information about the current world.

        :returns:
            A dict with these items:
                * name - The world name
                * size - The dimensions of the world
                * time - The current time in the world
                * daytime - Bool value indicating whether it is daytime or not
                * bloodmoon - Bool value indicating whether there is a blood moon or not
                * invasionsize - The current invasion size

        **endpoint:** /world/read
        """
        data = await self._make_request(self.urls.get_url("world", "read"))
        return data

    async def fetch_group_list(self):
        """Returns a list of all of the groups on the server.

        :returns:
            A dict with these items:
                * groups - An array of the groups configured on the server including:
                    * name
                    * parent
                    * chatcolor

        **endpoint:** /v2/groups/list
        """
        data = await self._make_request(self.urls.get_url("v2", "groups", "list"))
        return data
    async def fetch_group_info(self, group : str):
        """Returns info about a specific group.

        :param str group:
            The group to search for.

        :returns:
            A dict with these items:
                * name - The name of the group
                * parent - The name of the parent of this group
                * chatcolor - The chat color of this group
                * permissions - An array of permissions assigned "directly" to this group
                * negatedpermissions - An array of negated permissions assigned "directly" to this group
                * totalpermissions - An array of the calculated permissions available to members of this group
                                     due to direct permissions and inherited permissions

        **endpoint:** /v2/groups/read
        """
        data = await self._make_request(self.urls.get_url("v2", "groups", "read", group=group))
        return data

    async def fetch_server_motd(self):
        """Gets the server's MOTD.

        :returns:
            A dict with these items:
                * motd - The server's Message of the Day

        **endpoint:** /v3/server/motd
        """
        data = await self._make_request(self.urls.get_url("v3", "server", "motd"))
        return data

    async def fetch_server_rules(self):
        """Gets the server's rules.

        :returns:
            A dict with these items:
                * rules - The server rules

        **endpoint:** /v3/server/rules
        """
        data = await self._make_request(self.urls.get_url("v3", "server", "rules"))
        return data

    async def do_destroy_token(self):
        """Destroys the token being used by this class.

        **endpoint:** /token/destroy
        """
        await self._make_request(self.urls.get_url("token", "destroy", self.urls.token))

    async def do_destroy_all_tokens(self):
        """Destroys all tokens registered with the server.

        **endpoint:** /v3/token/destroy/all
        """
        await self._make_request(self.urls.get_url("v3", "token", "destroy", "all"))

    async def do_server_broadcast(self, message : str):
        """Broadcasts a message to all users on the server.

        :param str message:
            The message to be broadcasted.

        **endpoint:** /v2/server/broadcast
        """
        await self._make_request(self.urls.get_url("v2", "server", "broadcast", msg=message))

    async def do_server_reload(self):
        """Reloads the config file, permissions, and regions of the server.

        **endpoint:** /v3/server/reload
        """
        await self._make_request(self.urls.get_url("v3", "server", "reload"))

    async def do_server_off(self, confirm: bool = True, nosave: bool = False):
        """Shuts down the server.

        :param bool confirm:
            Do you realy want do off server?
            Usually True

        :param bool nosave:
            Off server without save or not?
            Usually False
            
        **endpoint:** /v2/server/off
        """
        await self._make_request(self.urls.get_url("v2", "server", "off", confirm=confirm, nosave=nosave))

    async def do_server_restart(self):
        """Restarts the server.

        **endpoint:** /v3/server/restart
        """
        await self._make_request(self.urls.get_url("v3", "server", "restart"))

    async def do_server_rawcmd(self, command : str):
        """Executes a command on the server and returns the output.

        :param str command:
            The command to be executed.

        :returns:
            A dict with these items:
                * response - The output of the command as an array of strings.

        **endpoint:** /v3/server/rawcmd
        """
        data = await self._make_request(self.urls.get_url("v3", "server", "rawcmd", cmd=command))
        return data

    async def do_create_ban(self, ip : str, name : str, reason : str):
        """Bans a user.

        :param str ip:
            The ip address to ban. Is required.

        :param str name:
            The player name to ban. May be an empty string.

        :param str reason:
            The reason the player was banned. May be an empty string.

        **endpoint:** /bans/create
        """
        await self._make_request(self.urls.get_url("bans", "create", ip=ip, name=name, reason=reason))

    async def do_delete_ban(self, type : BanLookupType, ban : str):
        """Deletes a ban.

        :param BanLookupType type:
            Defines how to search for the ban to be deleted.

        :param str ban:
            The ban to delete.

        **endpoint:** /v2/bans/destroy
        """
        await self._make_request(self.urls.get_url("v2", "bans", "destroy", ban=ban, type=type))

    async def do_world_meteor(self):
        """Drops a meteor on the world.

        **endpoint:** /world/meteor
        """
        await self._make_request(self.urls.get_url("world", "meteor"))

    async def do_world_save(self):
        """Saves the world. (No, not like Superman.)

        **endpoint:** /v2/world/save
        """
        await self._make_request(self.urls.get_url("v2", "world", "save"))

    async def do_world_butcher(self, killFriendly : bool):
        """Butchers all NPCs. Will never kill town NPCs, even if killFriendly
        is enabled.

        :param bool killFriendly:
            Whether to kill friendly mobs or not, such as bunnies.

        **endpoint:** /v2/world/butcher
        """
        await self._make_request(self.urls.get_url("v2", "world", "butcher", killfriendly=killFriendly))

    async def do_kick_player(self, player : str, reason : str):
        """Kicks a player.

        :param str reason:
            The reason the player was kicked.

        **endpoint:** /v2/players/kick
        """
        await self._make_request(self.urls.get_url("v2", "players", "kick", reason=reason, player=player))

    async def do_ban_player(self, player : str, reason : str):
        """Bans a player permanently.

        :param str player:
            Player to be banned.

        :param reason:
            Reason for the ban.

        **endpoint:** /v2/players/ban
        """
        await self._make_request(self.urls.get_url("v2", "players", "ban", reason=reason, player=player))

    async def do_kill_player(self, player : str, killer : str):
        """Kills a player.

        :param player:
            Player to be killed.

        :param killer:
            Person who 'killed' the player. This is displayed as "{killer} just killed you!"
            to the player.

        **endpoint:** /v2/players/kill
        """
        await self._make_request(self.urls.get_url("v2", "players", "kill", player=player, **{"from":killer}))

    async def do_mute_player(self, player : str):
        """Mutes a player.

        :param str player:
            Player to be muted.

        **endpoint:** /v2/players/mute
        """
        await self._make_request(self.urls.get_url("v2", "players", "mute", player=player))

    async def do_unmute_player(self, player : str):
        """Unmutes a player.

        :param str player:
            Player to be unmuted.

        **endpoint:** /v2/players/unmute
        """
        await self._make_request(self.urls.get_url("v2", "players", "unmute", player=player))

    async def do_group_delete(self, group : str):
        """Deletes a group.

        :param str group:
            The group to be deleted.

        **endpoint:** /v2/groups/destroy
        """
        await self._make_request(self.urls.get_url("v2", "groups", "destroy", group=group))

    async def do_group_create(self, group : str, parent : str = "", permissions : str = "", chatColor : str = "255,255,255"):
        """Adds a new group. Includes specification of parent, permissions, and chat color.

        :param str group:
            The name of the group to be created.

        :param str parent:
            The parent of the group to be created.

        :param str permissions:
            The permissions that the group should have as CSV.

        :param str chatColor:
            The group's chat color as three CSV RGB byte values.

        **endpoint:** /v2/groups/create
        """
        await self._make_request(self.urls.get_url("v2", "groups", "create",
                                             group=group,
                                             parent=parent,
                                             permissions=permissions,
                                             chatcolor=chatColor))

    async def do_create_user(self, lookup: UserLookupType, user : str, password: str, group: str):
        """Create user.

        :param UserLookupType type:
            The method in which to lookup the user.

        :param user str:
            Name of user you want to create

        :param password str:
            Password of user you want to create

        :param group str:
            Group of user you want to create        

        **endpoint:** /v2/users/create
        """
        await self._make_request(self.urls.get_url("v2", "users", "create", type=lookup.value, user=user, password=password, group=group))
        
    async def set_update_user(self, user : str, type : UserLookupType, password : str, group : str):
        """Updates a user in the TShock DB.

        :param str user:
            The search string, depending on the the lookup type.

        :param UserLookupType type:
            The method in which to lookup the user.

        :param str password:
            The new password for the user.

        :param str group:
            The new group for the user.

        **endpoint:** /v2/users/update
        """
        await self._make_request(self.urls.get_url("v2", "users", "update",
                                             user=user,
                                             type=type.value,
                                             password=password,
                                             group=group))

    async def set_world_bloodmoon(self, bloodmoon : bool):
        """Sets the world's bloodmoon.

        :param bool bloodmoon:
            Bool indicating what to set the bloodmoon to.

        **endpoint:** /world/bloodmoon/{bool}
        """
        await self._make_request(self.urls.get_url("world", "bloodmoon", bloodmoon))

    async def set_world_autosaving(self, autosave : bool):
        """Turns autosaving on or off.

        :param bool autosave:
            Bool indicating whether to turn autosaving on or off.

        **endpoint:** /v2/world/autosave/state/{bool}
        """
        await self._make_request(self.urls.get_url("v2", "world", "autosave", "state", autosave))

    async def set_group_update(self, group : str, parent : str = None, chatcolor : str = None, permissions : str = None):
        """Updates a group in the TShock DB.

        :param str group:
            The group to be updated.

        :param str parent:
            (Optional) The new parent of the group.

        :param str chatcolor:
            (Optional) The new group chatcolor as CSV RGB byte values.

        :param str permissions:
            (Optional) The new group permissions as a CSV string.

        **endpoint:** /v2/groups/update
        """
        if parent is None:
            parent = ""
        if chatcolor is None:
            chatcolor = ""
        if permissions is None:
            permissions = ""
        await self._make_request(self.urls.get_url("v2", "groups", "update",
                                             group=group,
                                             parent=parent,
                                             chatcolor=chatcolor,
                                             permissions=permissions))

class RequestBuilder():
    def __init__(self, ip, post):
        self.ip = ip
        self.post = post
        self.token = ""

    def get_url(self, *args, **kwargs) -> str:
        base = "http://{0}:{1}".format(self.ip, self.post)
        path = "/" + "/".join(args)
        kwargs['token'] = self.token

        params = urlencode(kwargs)
        return "{0}?{1}".format(urljoin(base, path), params)

"""Channel control commands (ch, bus, lr, dca, fx, rtn)."""

from dataclasses import dataclass
from typing import Optional, Callable, Any

import click

from xair.context import pass_context
from xair.utils import parse_channel_spec, parse_fader_value


@dataclass(frozen=True)
class PropSpec:
    subobj: Optional[str]
    attr: str
    convert: Callable[[str], Any]


@click.command("ch")
@click.argument("channel_spec")
@click.argument("args", nargs=-1)
@pass_context
def channel_cmd(ctx, channel_spec, args):
    """Control input channels.

    \b
    CHANNEL can be:
        1       Single channel
        1-4     Range of channels
        1,3,5   List of channels
        all     All channels

    \b
    PROPERTIES:
        fader    Level in dB (-90 to +10), supports +N/--N for relative
        mute     on|off|toggle
        name     Channel name (string)
        gain     Preamp gain in dB (0-60)
        phantom  on|off (48V phantom power)
        pan      -100 (L) to +100 (R)
        eq       on|off (EQ enable)
        gate     on|off (gate enable)
        comp     on|off (compressor enable)
        send.N   Send level to bus N in dB

    \b
    EXAMPLES:
        xair ch 1 fader -6        # Set fader to -6 dB
        xair ch 1 fader           # Get current fader value
        xair ch 1-4 mute on       # Mute channels 1-4
        xair ch all mute toggle   # Toggle mute on all channels
        xair ch 1,3,5 fader +3    # Increase fader by 3 dB
        xair ch 1 send.1 -10      # Set send to bus 1
    """
    ctx.connect()
    try:
        channels = parse_channel_spec(channel_spec, len(ctx.mixer.strip))
        for ch in channels:
            _channel_control(ctx, "strip", ch, args)
    except ValueError as e:
        raise click.ClickException(str(e))
    finally:
        ctx.disconnect()


@click.command("bus")
@click.argument("bus_spec")
@click.argument("args", nargs=-1)
@pass_context
def bus_cmd(ctx, bus_spec, args):
    """Control output buses.

    \b
    BUS can be:
        1       Single bus
        1-4     Range of buses
        1,3,5   List of buses
        all     All buses

    \b
    PROPERTIES:
        fader    Level in dB (-90 to +10), supports +N/--N for relative
        mute     on|off|toggle
        name     Bus name (string)
        pan      -100 (L) to +100 (R)
        eq       on|off (EQ enable)
        comp     on|off (compressor enable)

    \b
    EXAMPLES:
        xair bus 1 fader 0        # Set bus 1 to unity
        xair bus 1 mute off       # Unmute bus
        xair bus all mute on      # Mute all buses
        xair bus 1-4 fader --3    # Decrease all by 3 dB
    """
    ctx.connect()
    try:
        buses = parse_channel_spec(bus_spec, len(ctx.mixer.bus))
        for bus_num in buses:
            _channel_control(ctx, "bus", bus_num, args)
    except ValueError as e:
        raise click.ClickException(str(e))
    finally:
        ctx.disconnect()


@click.command("lr")
@click.argument("args", nargs=-1)
@pass_context
def lr_cmd(ctx, args):
    """Control main L/R output.

    \b
    EXAMPLES:
        xair lr fader -3          # Set main output to -3 dB
        xair lr mute on           # Mute main output
    """
    ctx.connect()
    try:
        _channel_control(ctx, "lr", None, args)
    finally:
        ctx.disconnect()


@click.command("dca")
@click.argument("dca_spec")
@click.argument("args", nargs=-1)
@pass_context
def dca_cmd(ctx, dca_spec, args):
    """Control DCA groups.

    \b
    DCA can be:
        1       Single DCA
        1-4     Range of DCAs
        all     All DCAs

    \b
    EXAMPLES:
        xair dca 1 mute off       # Unmute DCA 1
        xair dca all mute on      # Mute all DCAs
        xair dca 1 fader 0        # Set DCA fader
    """
    ctx.connect()
    try:
        dcas = parse_channel_spec(dca_spec, len(ctx.mixer.dca))
        for dca_num in dcas:
            _channel_control(ctx, "dca", dca_num, args)
    except ValueError as e:
        raise click.ClickException(str(e))
    finally:
        ctx.disconnect()


@click.command("fx")
@click.argument("fx_spec")
@click.argument("args", nargs=-1)
@pass_context
def fx_cmd(ctx, fx_spec, args):
    """Control FX slots.

    \b
    EXAMPLES:
        xair fx 1 type 5          # Set FX type
        xair fx all               # Show all FX slots
    """
    ctx.connect()
    try:
        fxs = parse_channel_spec(fx_spec, len(ctx.mixer.fx))
        for fx_num in fxs:
            _channel_control(ctx, "fx", fx_num, args)
    except ValueError as e:
        raise click.ClickException(str(e))
    finally:
        ctx.disconnect()


@click.command("rtn")
@click.argument("rtn_spec")
@click.argument("args", nargs=-1)
@pass_context
def rtn_cmd(ctx, rtn_spec, args):
    """Control FX returns.

    \b
    EXAMPLES:
        xair rtn 1 fader -6       # Set FX return level
        xair rtn all mute off     # Unmute all FX returns
    """
    ctx.connect()
    try:
        rtns = parse_channel_spec(rtn_spec, len(ctx.mixer.fxreturn))
        for rtn_num in rtns:
            _channel_control(ctx, "fxreturn", rtn_num, args)
    except ValueError as e:
        raise click.ClickException(str(e))
    finally:
        ctx.disconnect()


def _channel_control(ctx, channel_type: str, num: Optional[int], args: tuple) -> None:
    """Generic channel control logic."""
    if channel_type != "lr" and num is None:
        raise click.ClickException("Channel number is required")
    if channel_type == "lr":
        obj = ctx.mixer.lr
    elif channel_type == "strip":
        assert num is not None
        if not 1 <= num <= len(ctx.mixer.strip):
            raise click.ClickException(
                f"Channel {num} out of range (1-{len(ctx.mixer.strip)})"
            )
        obj = ctx.mixer.strip[num - 1]
    elif channel_type == "bus":
        assert num is not None
        if not 1 <= num <= len(ctx.mixer.bus):
            raise click.ClickException(
                f"Bus {num} out of range (1-{len(ctx.mixer.bus)})"
            )
        obj = ctx.mixer.bus[num - 1]
    elif channel_type == "dca":
        assert num is not None
        if not 1 <= num <= len(ctx.mixer.dca):
            raise click.ClickException(
                f"DCA {num} out of range (1-{len(ctx.mixer.dca)})"
            )
        obj = ctx.mixer.dca[num - 1]
    elif channel_type == "fx":
        assert num is not None
        if not 1 <= num <= len(ctx.mixer.fx):
            raise click.ClickException(f"FX {num} out of range (1-{len(ctx.mixer.fx)})")
        obj = ctx.mixer.fx[num - 1]
    elif channel_type == "fxreturn":
        assert num is not None
        if not 1 <= num <= len(ctx.mixer.fxreturn):
            raise click.ClickException(
                f"FX Return {num} out of range (1-{len(ctx.mixer.fxreturn)})"
            )
        obj = ctx.mixer.fxreturn[num - 1]
    else:
        raise click.ClickException(f"Unknown channel type: {channel_type}")

    if not args:
        data = _get_channel_props(obj, channel_type)
        ctx.output(data)
        return

    prop = args[0]
    value = args[1] if len(args) > 1 else None

    result = _access_property(obj, prop, value, channel_type, num, ctx)
    if result is not None:
        ctx.output(result)


def _get_channel_props(obj, channel_type: str) -> dict[str, object]:
    """Get common properties for a channel."""
    props = {}

    if hasattr(obj, "config"):
        props["name"] = obj.config.name
        props["color"] = obj.config.color

    if hasattr(obj, "mix"):
        props["fader"] = obj.mix.fader
        props["on"] = obj.mix.on

    if hasattr(obj, "on"):
        props["on"] = obj.on

    if hasattr(obj, "name"):
        props["name"] = obj.name

    if hasattr(obj, "fader"):
        props["fader"] = obj.fader

    return props


def _access_property(
    obj, prop: str, value: Optional[str], channel_type: str, num: Optional[int], ctx
) -> Optional[dict[str, object]]:
    """Access a property on a channel object (get or set)."""
    prop_map: dict[str, PropSpec] = {
        "fader": PropSpec("mix", "fader", float),
        "mute": PropSpec("mix", "on", lambda v: v.lower() not in ("on", "true", "1")),
        "on": PropSpec("mix", "on", lambda v: v.lower() in ("on", "true", "1")),
        "lr": PropSpec("mix", "lr", lambda v: v.lower() in ("on", "true", "1")),
        "pan": PropSpec("mix", "pan", float),
        "name": PropSpec("config", "name", str),
        "color": PropSpec("config", "color", int),
        "eq": PropSpec("eq", "on", lambda v: v.lower() in ("on", "true", "1")),
        "gate": PropSpec("gate", "on", lambda v: v.lower() in ("on", "true", "1")),
        "comp": PropSpec("dyn", "on", lambda v: v.lower() in ("on", "true", "1")),
        "type": PropSpec(None, "type", int),
    }

    # Handle gain and phantom via headamp
    if prop == "gain" and channel_type == "strip":
        if num is None:
            raise click.ClickException("Channel number is required for gain")
        headamp = ctx.mixer.headamp[num - 1]
        if value is None:
            return {"gain": headamp.gain, "unit": "dB"}
        headamp.gain = float(value)
        if not ctx.quiet:
            click.echo(f"gain = {value} dB")
        return None

    if prop == "phantom" and channel_type == "strip":
        if num is None:
            raise click.ClickException("Channel number is required for phantom")
        headamp = ctx.mixer.headamp[num - 1]
        if value is None:
            return {"phantom": headamp.phantom}
        headamp.phantom = value.lower() in ("on", "true", "1")
        if not ctx.quiet:
            click.echo(f"phantom = {value}")
        return None

    # Handle send.<N>
    if prop.startswith("send."):
        send_num = int(prop.split(".")[1])
        if not hasattr(obj, "send"):
            raise click.ClickException("Channel type does not support sends")
        if not 1 <= send_num <= len(obj.send):
            raise click.ClickException(f"Send {send_num} out of range")
        send = obj.send[send_num - 1]
        if value is None:
            return {"send": send_num, "level": send.level, "unit": "dB"}
        current = send.level
        new_value, is_relative = parse_fader_value(value, current)
        send.level = new_value
        if not ctx.quiet:
            if is_relative:
                click.echo(f"send.{send_num} = {new_value:.1f} dB ({value})")
            else:
                click.echo(f"send.{send_num} = {new_value:.1f} dB")
        return None

    if prop not in prop_map:
        raise click.ClickException(f"Unknown property '{prop}'")

    spec = prop_map[prop]

    if spec.subobj:
        if not hasattr(obj, spec.subobj):
            raise click.ClickException(
                f"Property '{prop}' not available for this channel type"
            )
        subobj = getattr(obj, spec.subobj)
    else:
        subobj = obj

    if value is None:
        val = getattr(subobj, spec.attr)
        if prop == "mute":
            val = not val
        unit = "dB" if prop in ("fader", "pan") else None
        result = {prop: val}
        if unit:
            result["unit"] = unit
        return result
    else:
        if prop == "fader":
            current = getattr(subobj, spec.attr)
            new_value, is_relative = parse_fader_value(value, current)
            setattr(subobj, spec.attr, new_value)
            if not ctx.quiet:
                if is_relative:
                    click.echo(f"{prop} = {new_value:.1f} dB ({value})")
                else:
                    click.echo(f"{prop} = {new_value:.1f} dB")
        else:
            converted = spec.convert(value)
            setattr(subobj, spec.attr, converted)
            if not ctx.quiet:
                click.echo(f"{prop} = {value}")
        return None

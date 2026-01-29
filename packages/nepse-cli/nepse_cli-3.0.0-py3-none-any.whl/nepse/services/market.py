"""
Market Data Service.
Handles fetching and displaying NEPSE market data from various APIs.
"""

import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich import box

from ..utils.formatting import format_number, format_rupees

console = Console(force_terminal=True, legacy_windows=False)


def get_ss_time() -> str:
    """Get timestamp from ShareSansar market summary."""
    try:
        response = requests.get("https://www.sharesansar.com/market-summary", timeout=10)
        soup = BeautifulSoup(response.text, "lxml")
        summary_cont = soup.find("div", id="market_symmary_data")
        if summary_cont is not None:
            msdate = summary_cont.find("h5").find("span")
            if msdate is not None:
                return msdate.text
    except:
        pass
    return "N/A"


def cmd_ipo() -> None:
    """Display all open IPOs/public offerings (all types)."""
    try:
        with console.status("[bold green]Fetching open IPOs...", spinner="dots"):
            response = requests.get(
                "https://sharehubnepal.com/data/api/v1/public-offering",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        
        if not data.get('success'):
            console.print(Panel(
                "⚠️  Unable to fetch IPO data. API request failed.",
                style="bold red",
                box=box.ROUNDED
            ))
            return
        
        all_ipos = data.get('data', {}).get('content', [])
        
        # Get all open IPOs (no filtering by type)
        open_ipos = [
            ipo for ipo in all_ipos 
            if ipo.get('status') == 'Open'
        ]
        
        if not open_ipos:
            console.print(Panel(
                "💤 No IPOs are currently open for subscription.",
                style="bold yellow",
                box=box.ROUNDED
            ))
            return
        
        table = Table(
            title=f"📈 Open IPOs ({len(open_ipos)})",
            box=box.ROUNDED,
            header_style="bold cyan",
            expand=True
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Company", style="bold white")
        table.add_column("IPO Type", style="magenta")
        table.add_column("For", style="cyan")
        table.add_column("Units", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Closing", style="yellow")
        table.add_column("Status", justify="center")
        
        # Type display mapping with emojis
        type_display_map = {
            'Ipo': '🆕 IPO',
            'Fpo': '📊 FPO',
            'Right': '🔄 Right',
            'MutualFund': '💼 Mutual Fund',
            'BondOrDebenture': '💰 Bond/Deb'
        }
        
        # For (target group) display mapping
        for_display_map = {
            'GeneralPublic': 'General',
            'ForeignEmployment': 'Foreign Emp.',
            'LocalPeople': 'Local'
        }
        
        for index, ipo in enumerate(open_ipos, 1):
            symbol = ipo.get('symbol', 'N/A')
            name = ipo.get('name', 'N/A')
            units = ipo.get('units', 0)
            price = ipo.get('price', 0)
            closing_date = ipo.get('closingDate', 'N/A')
            extended_closing = ipo.get('extendedClosingDate', None)
            ipo_type = ipo.get('type', 'N/A')
            ipo_for = ipo.get('for', 'N/A')
            
            try:
                closing_date_obj = datetime.fromisoformat(closing_date.replace('T', ' '))
                closing_date_str = closing_date_obj.strftime('%d %b')
            except:
                closing_date_str = closing_date
            
            # Calculate urgency
            urgency_text = ""
            urgency_style = "white"
            
            try:
                target_date = extended_closing if extended_closing else closing_date
                target_date_obj = datetime.fromisoformat(target_date.replace('T', ' '))
                days_left = (target_date_obj - datetime.now()).days
                
                if days_left >= 0:
                    if days_left <= 2:
                        urgency_text = f"⚠️ {days_left}d left"
                        urgency_style = "bold red"
                    elif days_left <= 5:
                        urgency_text = f"⏰ {days_left}d left"
                        urgency_style = "yellow"
                    else:
                        urgency_text = f"📅 {days_left}d"
                        urgency_style = "green"
            except:
                urgency_text = "Check dates"
            
            type_display = type_display_map.get(ipo_type, ipo_type)
            for_display = for_display_map.get(ipo_for, ipo_for)
            
            table.add_row(
                str(index),
                f"{symbol}\n[dim]{name}[/dim]",
                type_display,
                for_display,
                f"{units:,}",
                format_rupees(price),
                closing_date_str,
                f"[{urgency_style}]{urgency_text}[/{urgency_style}]"
            )
        
        console.print(table)
        console.print(Panel(
            "💡 Tip: Use [bold cyan]apply[/] to apply for IPO via Meroshare",
            box=box.ROUNDED,
            style="dim"
        ))
        
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]🔌 Connection Error:[/bold red] {str(e)[:100]}\n")
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)[:200]}\n")


def cmd_nepse() -> None:
    """Display NEPSE indices data."""
    try:
        with console.status("[bold green]Fetching NEPSE indices...", spinner="dots"):
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            
            url = "https://nepsealpha.com/live/stocks"
            response = scraper.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Fetch ShareHub data
            market_status = "UNKNOWN"
            market_summary = None
            stock_summary = None
            try:
                sharehub_response = requests.get(
                    "https://sharehubnepal.com/live/api/v2/nepselive/home-page-data",
                    timeout=10
                )
                if sharehub_response.status_code == 200:
                    sharehub_data = sharehub_response.json()
                    market_status_obj = sharehub_data.get('marketStatus', {})
                    market_status = market_status_obj.get('status', 'UNKNOWN')
                    market_summary = sharehub_data.get('marketSummary', [])
                    stock_summary = sharehub_data.get('stockSummary', {})
            except:
                pass
        
        prices = data.get('stock_live', {}).get('prices', [])
        indices = [item for item in prices if item.get('stockinfo', {}).get('type') == 'index']
        
        if not indices:
            console.print(Panel(
                "⚠️  No index data available.",
                style="bold yellow",
                box=box.ROUNDED
            ))
            return
        
        timestamp = data.get('stock_live', {}).get('asOf', 'N/A')
        
        # Market status indicator
        if market_status == "OPEN":
            status_indicator = "[bold green]●[/bold green] OPEN"
            status_color = "green"
        elif market_status == "CLOSE":
            status_indicator = "[bold red]●[/bold red] CLOSE"
            status_color = "red"
        else:
            status_indicator = "[bold yellow]●[/bold yellow] UNKNOWN"
            status_color = "yellow"
        
        # Separate main and sub indices
        main_index_names = ['NEPSE', 'SENSITIVE', 'FLOAT', 'SENFLOAT']
        main_indices = [item for item in indices if item.get('symbol', '') in main_index_names]
        sub_indices = [item for item in indices if item.get('symbol', '') not in main_index_names]
        
        main_order = {name: idx for idx, name in enumerate(main_index_names)}
        main_indices.sort(key=lambda x: main_order.get(x.get('symbol', ''), 999))
        
        # Main Indices Table
        main_table = Table(
            title=f"📊 Main Indices (Live) - {timestamp} | Market: {status_indicator}",
            box=box.ROUNDED,
            header_style="bold cyan",
            border_style=status_color
        )
        main_table.add_column("Index", style="bold white", width=16)
        main_table.add_column("Open", justify="right")
        main_table.add_column("Close", justify="right")
        main_table.add_column("Change", justify="right")
        main_table.add_column("% Change", justify="right")
        main_table.add_column("Trend", justify="center")
        main_table.add_column("Range (L-H)", justify="center", style="dim")
        main_table.add_column("Turnover", justify="right")
        
        for item in main_indices:
            index_name = item.get('symbol', 'N/A')
            open_val = item.get('open', 0)
            close_val = item.get('close', 0)
            pct_change = item.get('percent_change', 0)
            low_val = item.get('low', 0)
            high_val = item.get('high', 0)
            turnover = item.get('volume', 0)
            
            try:
                if pct_change != 0 and close_val != 0:
                    prev_close = close_val / (1 + pct_change / 100)
                    point_change = close_val - prev_close
                else:
                    point_change = 0
            except:
                point_change = 0
            
            color = "green" if pct_change > 0 else "red" if pct_change < 0 else "yellow"
            trend_icon = "▲" if pct_change > 0 else "▼" if pct_change < 0 else "•"
            range_str = f"{low_val:,.2f} - {high_val:,.2f}"
            
            main_table.add_row(
                index_name,
                f"{open_val:,.2f}",
                f"{close_val:,.2f}",
                f"[{color}]{point_change:+,.2f}[/{color}]",
                f"[{color}]{pct_change:+.2f}%[/{color}]",
                f"[{color}]{trend_icon}[/{color}]",
                range_str,
                format_number(turnover)
            )
        
        console.print(main_table)
        
        # Market Overview
        if market_summary:
            console.print("\n")
            market_table = Table(
                title="💰 Market Overview",
                box=box.ROUNDED,
                header_style="bold cyan",
                border_style="cyan"
            )
            
            for item in market_summary:
                metric_name = item.get('name', 'N/A')
                short_name = metric_name.replace('Total ', '').replace(' Rs:', '').replace(':', '')
                market_table.add_column(short_name, justify="right", style="cyan")
            
            row_values = []
            for item in market_summary:
                metric_value = item.get('value', 0)
                metric_name = item.get('name', 'N/A')
                
                if 'Turnover' in metric_name:
                    formatted_value = f"Rs. {metric_value:,.2f}"
                elif any(x in metric_name for x in ['Shares', 'Transactions', 'Scripts']):
                    formatted_value = f"{int(metric_value):,}"
                else:
                    formatted_value = f"{metric_value:,}"
                
                row_values.append(formatted_value)
            
            market_table.add_row(*row_values)
            console.print(market_table)
        
        # Stock Movement
        if stock_summary:
            console.print("\n")
            stock_table = Table(
                title="📊 Stock Movement",
                box=box.ROUNDED,
                header_style="bold magenta",
                border_style="magenta"
            )
            
            stock_table.add_column("Advanced", justify="center", style="bold green")
            stock_table.add_column("Declined", justify="center", style="bold red")
            stock_table.add_column("Unchanged", justify="center", style="bold yellow")
            stock_table.add_column("Positive Circuit", justify="center")
            stock_table.add_column("Negative Circuit", justify="center")
            
            advanced = stock_summary.get('advanced', 0)
            declined = stock_summary.get('declined', 0)
            unchanged = stock_summary.get('unchanged', 0)
            positive_circuit = stock_summary.get('positiveCircuit', 0)
            negative_circuit = stock_summary.get('negativeCircuit', 0)
            
            pos_circuit_color = "bright_green" if positive_circuit > 0 else "dim"
            neg_circuit_color = "bright_red" if negative_circuit > 0 else "dim"
            
            stock_table.add_row(
                f"{advanced:,}",
                f"{declined:,}",
                f"{unchanged:,}",
                f"[{pos_circuit_color}]{positive_circuit:,}[/{pos_circuit_color}]",
                f"[{neg_circuit_color}]{negative_circuit:,}[/{neg_circuit_color}]"
            )
            
            console.print(stock_table)
        
        # Sub-Indices
        if sub_indices:
            console.print("\n")
            sub_table = Table(
                title="📈 Sub-Indices",
                box=box.ROUNDED,
                header_style="bold magenta"
            )
            sub_table.add_column("Index", style="bold white")
            sub_table.add_column("Close", justify="right")
            sub_table.add_column("Change", justify="right")
            sub_table.add_column("% Change", justify="right")
            sub_table.add_column("Trend", justify="center")
            sub_table.add_column("Range (L-H)", justify="center", style="dim")
            
            for item in sub_indices:
                index_name = item.get('symbol', 'N/A')
                close_val = item.get('close', 0)
                pct_change = item.get('percent_change', 0)
                low_val = item.get('low', 0)
                high_val = item.get('high', 0)
                
                try:
                    if pct_change != 0 and close_val != 0:
                        prev_close = close_val / (1 + pct_change / 100)
                        point_change = close_val - prev_close
                    else:
                        point_change = 0
                except:
                    point_change = 0
                
                color = "green" if pct_change > 0 else "red" if pct_change < 0 else "yellow"
                trend_icon = "▲" if pct_change > 0 else "▼" if pct_change < 0 else "•"
                range_str = f"{low_val:,.2f} - {high_val:,.2f}"
                
                sub_table.add_row(
                    index_name,
                    f"{close_val:,.2f}",
                    f"[{color}]{point_change:+,.2f}[/{color}]",
                    f"[{color}]{pct_change:+.2f}%[/{color}]",
                    f"[{color}]{trend_icon}[/{color}]",
                    range_str
                )
            
            console.print(sub_table)
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error fetching NEPSE data:[/bold red] {str(e)}\n")


def cmd_subidx(subindex_name: str) -> None:
    """Display sub-index details."""
    try:
        subindex_name = subindex_name.upper()
        
        sub_index_mapping = {
            "BANKING": "BANKING",
            "DEVBANK": "DEVBANK",
            "FINANCE": "FINANCE",
            "HOTELS AND TOURISM": "HOTELS",
            "HOTELS": "HOTELS",
            "HYDROPOWER": "HYDROPOWER",
            "INVESTMENT": "INVESTMENT",
            "LIFE INSURANCE": "LIFEINSU",
            "LIFEINSU": "LIFEINSU",
            "MANUFACTURING AND PROCESSING": "MANUFACTURE",
            "MANUFACTURE": "MANUFACTURE",
            "MICROFINANCE": "MICROFINANCE",
            "MUTUAL FUND": "MUTUAL",
            "MUTUAL": "MUTUAL",
            "NONLIFE INSURANCE": "NONLIFEINSU",
            "NONLIFEINSU": "NONLIFEINSU",
            "OTHERS": "OTHERS",
            "TRADING": "TRADING",
        }
        
        with console.status(f"[bold green]Fetching {subindex_name} data...", spinner="dots"):
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            response = scraper.get("https://nepsealpha.com/live/stocks", timeout=10)
            response.raise_for_status()
            data = response.json()
        
        search_symbol = sub_index_mapping.get(subindex_name, subindex_name)
        
        prices = data.get('stock_live', {}).get('prices', [])
        indices = [item for item in prices if item.get('stockinfo', {}).get('type') == 'index']
        
        sub_index_data = None
        for item in indices:
            if item.get('symbol', '').upper() == search_symbol.upper():
                sub_index_data = item
                break
        
        if not sub_index_data:
            console.print(Panel(
                f"⚠️  Sub-index '{subindex_name}' not found.",
                style="bold red",
                box=box.ROUNDED
            ))
            
            available = set()
            for item in indices:
                symbol = item.get('symbol', '')
                if symbol not in ['NEPSE', 'SENSITIVE', 'FLOAT']:
                    available.add(symbol)
            
            table = Table(title="Available Sub-Indices", box=box.ROUNDED)
            table.add_column("Symbol", style="cyan")
            for sym in sorted(available):
                table.add_row(sym)
            console.print(table)
            return
        
        sectors = data.get('sectors', {})
        sector_full_name = sectors.get(search_symbol, search_symbol)
        
        close_val = sub_index_data.get('close', 0)
        pct_change = sub_index_data.get('percent_change', 0)
        low_val = sub_index_data.get('low', 0)
        high_val = sub_index_data.get('high', 0)
        open_val = sub_index_data.get('open', 0)
        turnover = sub_index_data.get('volume', 0)
        
        try:
            if pct_change != 0 and close_val != 0:
                prev_close = close_val / (1 + pct_change / 100)
                point_change = close_val - prev_close
            else:
                point_change = 0
        except:
            point_change = 0
        
        color = "green" if pct_change > 0 else "red" if pct_change < 0 else "yellow"
        trend_icon = "▲" if pct_change > 0 else "▼" if pct_change < 0 else "•"
        
        timestamp = data.get('stock_live', {}).get('asOf', 'N/A')
        
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column(style="bold white")
        grid.add_column(justify="right")
        
        grid.add_row("Close Price", f"{close_val:,.2f}")
        grid.add_row("Change", f"[{color}]{point_change:+,.2f} ({pct_change:+.2f}%)[/{color}]")
        grid.add_row("Trend", f"[{color}]{trend_icon} {color.upper()}[/{color}]")
        grid.add_row("Range (Low-High)", f"{low_val:,.2f} - {high_val:,.2f}")
        grid.add_row("Open Price", f"{open_val:,.2f}")
        grid.add_row("Turnover", format_number(turnover))
        
        panel = Panel(
            grid,
            title=f"[bold {color}]{sector_full_name} ({search_symbol})[/]",
            subtitle=f"As of: {timestamp}",
            box=box.ROUNDED,
            border_style=color
        )
        console.print(panel)
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error fetching sub-index data:[/bold red] {str(e)}\n")


def cmd_topgl() -> None:
    """Display top 10 gainers and losers."""
    try:
        with console.status("[bold green]Fetching top gainers and losers...", spinner="dots"):
            response = requests.get("https://merolagani.com/LatestMarket.aspx", timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            tgtl_col = soup.find('div', class_="col-md-4 hidden-xs hidden-sm")
            tgtl_tables = tgtl_col.find_all('table')
            
            gainers = tgtl_tables[0]
            gainers_row = gainers.find_all('tr')
            
            losers = tgtl_tables[1]
            losers_row = losers.find_all('tr')
        
        # Gainers Table
        g_table = Table(
            title="📈 TOP 10 GAINERS",
            box=box.ROUNDED,
            header_style="bold green",
            expand=True
        )
        g_table.add_column("#", style="dim", width=4)
        g_table.add_column("Symbol", style="bold white")
        g_table.add_column("LTP", justify="right")
        g_table.add_column("%Chg", justify="right", style="green")
        g_table.add_column("High", justify="right", style="dim")
        g_table.add_column("Low", justify="right", style="dim")
        g_table.add_column("Volume", justify="right")
        
        for idx, tr in enumerate(gainers_row[1:], 1):
            tds = tr.find_all('td')
            if tds and len(tds) >= 8:
                medal = ["🥇", "🥈", "🥉"] + [""] * 7
                g_table.add_row(
                    f"{idx} {medal[idx-1]}",
                    tds[0].text,
                    tds[1].text,
                    f"+{tds[2].text}%",
                    tds[3].text,
                    tds[4].text,
                    format_number(tds[6].text)
                )
        
        # Losers Table
        l_table = Table(
            title="📉 TOP 10 LOSERS",
            box=box.ROUNDED,
            header_style="bold red",
            expand=True
        )
        l_table.add_column("#", style="dim", width=4)
        l_table.add_column("Symbol", style="bold white")
        l_table.add_column("LTP", justify="right")
        l_table.add_column("%Chg", justify="right", style="red")
        l_table.add_column("High", justify="right", style="dim")
        l_table.add_column("Low", justify="right", style="dim")
        l_table.add_column("Volume", justify="right")
        
        for idx, tr in enumerate(losers_row[1:], 1):
            tds = tr.find_all('td')
            if tds and len(tds) >= 8:
                l_table.add_row(
                    str(idx),
                    tds[0].text,
                    tds[1].text,
                    f"-{tds[2].text}%",
                    tds[3].text,
                    tds[4].text,
                    format_number(tds[6].text)
                )
        
        console.print(g_table)
        console.print(l_table)
        
        timestamp = get_ss_time()
        console.print(f"[dim]As of: {timestamp}[/dim]\n", justify="center")
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error fetching top gainers/losers:[/bold red] {str(e)}\n")


def cmd_stonk(stock_names: str) -> None:
    """Display stock details for one or multiple stocks."""
    try:
        # Parse multiple stock names (space or comma separated)
        import re
        stock_list = re.split(r'[,\s]+', stock_names.strip())
        stock_list = [s.upper() for s in stock_list if s]
        
        if not stock_list:
            console.print("[red]⚠️  No stock symbols provided.[/red]")
            return
        
        with console.status(f"[bold green]Fetching {len(stock_list)} stock(s)...", spinner="dots"):
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            
            response = scraper.get('https://nepsealpha.com/live/stocks', timeout=10)
            response.raise_for_status()
            data = response.json()
            
            prices = data.get('stock_live', {}).get('prices', [])
            timestamp = data.get('stock_live', {}).get('asOf', 'N/A')
        
        # Find data for each requested stock
        found_stocks = []
        not_found = []
        
        for stock_name in stock_list:
            stock_data = None
            for item in prices:
                if item.get('symbol', '').upper() == stock_name:
                    stock_data = item
                    break
            
            if stock_data:
                found_stocks.append((stock_name, stock_data))
            else:
                not_found.append(stock_name)
        
        # Display each stock
        for idx, (stock_name, stock_price_data) in enumerate(found_stocks):
            close_price = stock_price_data.get("close", 0)
            percent_change = stock_price_data.get("percent_change", 0)
            
            try:
                if percent_change != 0 and close_price != 0:
                    prev_close = close_price / (1 + percent_change / 100)
                    pt_change = close_price - prev_close
                else:
                    prev_close = close_price
                    pt_change = 0
            except:
                prev_close = close_price
                pt_change = 0
            
            color = "green" if pt_change > 0 else "red" if pt_change < 0 else "yellow"
            trend_icon = "▲" if pt_change > 0 else "▼" if pt_change < 0 else "•"
            
            grid = Table.grid(expand=True, padding=(0, 2))
            grid.add_column(style="bold white")
            grid.add_column(justify="right")
            
            grid.add_row("Last Traded Price", f"Rs. {close_price:,.2f}")
            grid.add_row("Change", f"[{color}]{pt_change:+,.2f} ({percent_change:+.2f}%) {trend_icon}[/{color}]")
            grid.add_row("Open", f"Rs. {stock_price_data.get('open', 0):,.2f}")
            grid.add_row("High", f"Rs. {stock_price_data.get('high', 0):,.2f}")
            grid.add_row("Low", f"Rs. {stock_price_data.get('low', 0):,.2f}")
            grid.add_row("Volume", f"{int(stock_price_data.get('volume', 0)):,}")
            grid.add_row("Prev. Closing", f"Rs. {prev_close:,.2f}")
            
            panel = Panel(
                grid,
                title=f"[bold {color}]{stock_name}[/]",
                subtitle=f"As of: {timestamp}",
                box=box.ROUNDED,
                border_style=color
            )
            console.print(panel)
            
            # Add spacing between stocks, but not after the last one
            if idx < len(found_stocks) - 1:
                console.print()
        
        # Show not found stocks
        if not_found:
            console.print()
            console.print(Panel(
                f"⚠️  Stock(s) not found: {', '.join(not_found)}",
                style="bold yellow",
                box=box.ROUNDED
            ))
        
        # Show chart link for single stock
        if len(found_stocks) == 1:
            chart_url = f"https://nepsealpha.com/trading/chart?symbol={found_stocks[0][0]}"
            console.print(f"\n[dim]📊 View Chart:[/dim] [link={chart_url}][cyan underline]{chart_url}[/cyan underline][/link]\n")
        elif found_stocks:
            console.print("\n[dim]💡 Tip: Use 'stonk <symbol>' with a single stock to view chart link[/dim]\n")
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error fetching stock data:[/bold red] {str(e)}\n")


def cmd_mktsum() -> None:
    """Display comprehensive market summary."""
    try:
        sharehub_data = None
        
        with console.status("[bold green]Fetching market data...", spinner="dots"):
            try:
                url = "https://sharehubnepal.com/live/api/v2/nepselive/home-page-data"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    sharehub_data = response.json()
            except Exception as e:
                console.print(f"[red]⚠️  API request failed: {e}[/red]")
            
            if not sharehub_data:
                return
        
        indices = sharehub_data.get("indices", [])
        nepse_index = next((i for i in indices if i.get("symbol") == "NEPSE"), {})
        
        if not nepse_index:
            console.print("[red]⚠️  NEPSE index data not found.[/red]")
            return
        
        current_price = float(nepse_index.get('currentValue', 0))
        daily_gain = float(nepse_index.get('changePercent', 0))
        
        # Market summary
        turnover = 0
        total_traded_shares = 0
        total_transactions = 0
        
        market_summary = sharehub_data.get("marketSummary", [])
        for item in market_summary:
            name = item.get('name', '')
            value = item.get('value', 0)
            if 'Turnover' in name:
                turnover = float(value)
            elif 'Traded Shares' in name:
                total_traded_shares = int(value)
            elif 'Transactions' in name:
                total_transactions = int(value)
        
        # Stock summary
        stock_summary = sharehub_data.get("stockSummary", {})
        positive_stocks = stock_summary.get("advanced", 0)
        negative_stocks = stock_summary.get("declined", 0)
        unchanged_stocks = stock_summary.get("unchanged", 0)
        positive_circuit = stock_summary.get("positiveCircuit", 0)
        negative_circuit = stock_summary.get("negativeCircuit", 0)
        total_traded = positive_stocks + negative_stocks + unchanged_stocks
        
        color = "green" if daily_gain > 0 else "red" if daily_gain < 0 else "yellow"
        trend_icon = "▲" if daily_gain > 0 else "▼" if daily_gain < 0 else "•"
        
        # NEPSE Table
        nepse_table = Table(
            title="📊 NEPSE Index",
            box=box.ROUNDED,
            header_style="bold cyan",
            border_style=color
        )
        
        nepse_table.add_column("Current Index", justify="right", style="bold white")
        nepse_table.add_column("Daily Gain", justify="right")
        nepse_table.add_column("Turnover", justify="right", style="cyan")
        
        if total_traded_shares > 0:
            nepse_table.add_column("Traded Shares", justify="right", style="cyan")
        if total_transactions > 0:
            nepse_table.add_column("Transactions", justify="right", style="cyan")
        
        row_values = [
            f"{current_price:,.2f}",
            f"[{color}]{daily_gain:+.2f}% {trend_icon}[/{color}]",
            format_number(turnover)
        ]
        
        if total_traded_shares > 0:
            row_values.append(format_number(total_traded_shares))
        if total_transactions > 0:
            row_values.append(format_number(total_transactions))
        
        nepse_table.add_row(*row_values)
        console.print(nepse_table)
        
        # Trading Activity
        console.print("\n")
        activity_table = Table(
            title="📈 Trading Activity",
            box=box.ROUNDED,
            header_style="bold magenta",
            border_style="magenta"
        )
        
        activity_table.add_column("Positive Stocks", justify="center", style="bold green")
        activity_table.add_column("Negative Stocks", justify="center", style="bold red")
        activity_table.add_column("Unchanged", justify="center", style="bold yellow")
        activity_table.add_column("Positive Circuit", justify="center")
        activity_table.add_column("Negative Circuit", justify="center")
        activity_table.add_column("Total Traded", justify="center", style="bold white")
        
        pos_circuit_color = "bright_green" if positive_circuit > 0 else "dim"
        neg_circuit_color = "bright_red" if negative_circuit > 0 else "dim"
        
        activity_table.add_row(
            f"{positive_stocks:,}",
            f"{negative_stocks:,}",
            f"{unchanged_stocks:,}",
            f"[{pos_circuit_color}]{positive_circuit:,}[/{pos_circuit_color}]",
            f"[{neg_circuit_color}]{negative_circuit:,}[/{neg_circuit_color}]",
            f"{total_traded:,}"
        )
        
        console.print(activity_table)
        
        # Sector Performance
        sub_indices = sharehub_data.get("subIndices", [])
        if sub_indices:
            console.print("\n")
            sector_table = Table(
                title="Sector Performance",
                box=box.ROUNDED,
                expand=True
            )
            sector_table.add_column("Sector", style="cyan")
            sector_table.add_column("Current", justify="right")
            sector_table.add_column("Change %", justify="right")
            
            for sector in sub_indices:
                name = sector.get("name", "Unknown")
                price = sector.get("currentValue", 0)
                change = sector.get("changePercent", 0)
                
                sec_color = "green" if change > 0 else "red" if change < 0 else "white"
                
                sector_table.add_row(
                    name,
                    f"{price:,.2f}",
                    f"[{sec_color}]{change:+.2f}%[/{sec_color}]"
                )
            
            console.print(sector_table)
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def get_dp_list() -> None:
    """Fetch and display available DP list from API."""
    try:
        with console.status("[bold green]Fetching DP list...", spinner="dots"):
            response = requests.get("https://webbackend.cdsc.com.np/api/meroShare/capital/")
            response.raise_for_status()
            dp_data = response.json()
            dp_data.sort(key=lambda x: x['name'])
        
        table = Table(
            title=f"Available Depository Participants (Total: {len(dp_data)})",
            box=box.ROUNDED,
            header_style="bold cyan"
        )
        table.add_column("ID", style="bold yellow", justify="right")
        table.add_column("Code", style="dim")
        table.add_column("Name", style="white")
        
        for dp in dp_data:
            table.add_row(str(dp['id']), str(dp['code']), dp['name'])
        
        console.print(table)
        console.print(Panel(
            "Note: Use the [bold yellow]ID[/] when setting up credentials",
            box=box.ROUNDED,
            style="dim"
        ))
        
    except requests.RequestException as e:
        console.print(f"[bold red]✗ Error fetching DP list:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]✗ Unexpected error:[/bold red] {e}\n")


def cmd_52week() -> None:
    """Display stocks at 52-week high/low."""
    try:
        with console.status("[bold green]Fetching 52-week data...", spinner="dots"):
            response = requests.get(
                "https://sharehubnepal.com/data/api/v1/price-history/52w-high-low",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        
        if not data.get('success'):
            console.print("[red]⚠️  Failed to fetch 52-week data[/red]")
            return
        
        stocks = data.get('data', [])
        
        if not stocks:
            console.print("[yellow]No 52-week data available[/yellow]")
            return
        
        # Separate into near high and near low
        near_high = []
        near_low = []
        
        for stock in stocks:
            ltp = stock.get('lastTradedPrice', 0)
            high_52 = stock.get('fiftyTwoWeekHigh', 0)
            low_52 = stock.get('fiftyTwoWeekLow', 0)
            
            if ltp > 0 and high_52 > 0 and low_52 > 0:
                # Calculate distance to high/low
                dist_to_high = ((high_52 - ltp) / high_52) * 100 if high_52 > 0 else 100
                dist_to_low = ((ltp - low_52) / low_52) * 100 if low_52 > 0 else 100
                
                # Near high if within 5% of 52-week high
                if dist_to_high <= 5:
                    near_high.append(stock)
                # Near low if within 5% of 52-week low
                elif dist_to_low <= 5:
                    near_low.append(stock)
        
        # Sort by proximity
        near_high.sort(key=lambda x: (x.get('fiftyTwoWeekHigh', 0) - x.get('lastTradedPrice', 0)) / x.get('fiftyTwoWeekHigh', 1) if x.get('fiftyTwoWeekHigh', 0) > 0 else 999)
        near_low.sort(key=lambda x: (x.get('lastTradedPrice', 0) - x.get('fiftyTwoWeekLow', 0)) / x.get('fiftyTwoWeekLow', 1) if x.get('fiftyTwoWeekLow', 0) > 0 else 999)
        
        # 52-Week High Table
        if near_high:
            high_table = Table(
                title=f"📈 Near 52-Week HIGH ({len(near_high)} stocks)",
                box=box.ROUNDED,
                header_style="bold green",
                expand=True
            )
            high_table.add_column("#", style="dim", width=4)
            high_table.add_column("Symbol", style="bold white")
            high_table.add_column("LTP", justify="right")
            high_table.add_column("52W High", justify="right", style="green")
            high_table.add_column("Gap", justify="right")
            high_table.add_column("Change %", justify="right")
            
            for idx, stock in enumerate(near_high[:15], 1):
                ltp = stock.get('lastTradedPrice', 0)
                high_52 = stock.get('fiftyTwoWeekHigh', 0)
                pct = stock.get('changePercentage', 0)
                gap = ((high_52 - ltp) / high_52 * 100) if high_52 > 0 else 0
                color = "green" if pct > 0 else "red" if pct < 0 else "white"
                high_table.add_row(
                    str(idx),
                    stock.get('symbol', 'N/A'),
                    f"Rs. {ltp:,.2f}",
                    f"Rs. {high_52:,.2f}",
                    f"{gap:.1f}%",
                    f"[{color}]{pct:+.2f}%[/{color}]"
                )
            console.print(high_table)
        else:
            console.print("[dim]No stocks near 52-week high[/dim]")
        
        console.print()
        
        # 52-Week Low Table
        if near_low:
            low_table = Table(
                title=f"📉 Near 52-Week LOW ({len(near_low)} stocks)",
                box=box.ROUNDED,
                header_style="bold red",
                expand=True
            )
            low_table.add_column("#", style="dim", width=4)
            low_table.add_column("Symbol", style="bold white")
            low_table.add_column("LTP", justify="right")
            low_table.add_column("52W Low", justify="right", style="red")
            low_table.add_column("Gap", justify="right")
            low_table.add_column("Change %", justify="right")
            
            for idx, stock in enumerate(near_low[:15], 1):
                ltp = stock.get('lastTradedPrice', 0)
                low_52 = stock.get('fiftyTwoWeekLow', 0)
                pct = stock.get('changePercentage', 0)
                gap = ((ltp - low_52) / low_52 * 100) if low_52 > 0 else 0
                color = "green" if pct > 0 else "red" if pct < 0 else "white"
                low_table.add_row(
                    str(idx),
                    stock.get('symbol', 'N/A'),
                    f"Rs. {ltp:,.2f}",
                    f"Rs. {low_52:,.2f}",
                    f"{gap:.1f}%",
                    f"[{color}]{pct:+.2f}%[/{color}]"
                )
            console.print(low_table)
        else:
            console.print("[dim]No stocks near 52-week low[/dim]")
            
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def cmd_near52() -> None:
    """Display stocks trading near 52-week high/low."""
    try:
        with console.status("[bold green]Fetching near 52-week data...", spinner="dots"):
            response = requests.get(
                "https://chukul.com/api/data/historydata/trading-near-52-week/",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        
        stocks = data.get('stock', []) if isinstance(data, dict) else data
        
        if not stocks:
            console.print("[yellow]No stocks trading near 52-week levels[/yellow]")
            return
        
        # Separate near high (within 5% of max) and near low (within 5% of min)
        near_high = []
        near_low = []
        
        for s in stocks:
            close = s.get('close', 0)
            max_close = s.get('max_close', 0)
            min_close = s.get('min_close', 0)
            below_max_pct = abs(s.get('below_max_percentage', 100))
            above_min_pct = s.get('above_min_percentage', 100)
            
            # Near 52-week high if within 5% of max
            if below_max_pct <= 5:
                near_high.append(s)
            # Near 52-week low if within 5% of min
            elif above_min_pct <= 5:
                near_low.append(s)
        
        # Sort by proximity
        near_high.sort(key=lambda x: abs(x.get('below_max_percentage', 100)))
        near_low.sort(key=lambda x: x.get('above_min_percentage', 100))
        
        # Near 52-Week High
        if near_high:
            table = Table(
                title=f"🔺 Near 52-Week HIGH ({len(near_high)} stocks)",
                box=box.ROUNDED,
                header_style="bold green"
            )
            table.add_column("Symbol", style="bold white")
            table.add_column("LTP", justify="right")
            table.add_column("52W High", justify="right", style="green")
            table.add_column("Gap", justify="right")
            
            for stock in near_high[:15]:
                ltp = stock.get('close', 0)
                high = stock.get('max_close', 0)
                gap = stock.get('below_max_percentage', 0)
                table.add_row(
                    stock.get('symbol', 'N/A'),
                    f"Rs. {ltp:,.2f}",
                    f"Rs. {high:,.2f}",
                    f"[green]{gap:.2f}%[/green]"
                )
            console.print(table)
        else:
            console.print("[dim]No stocks currently near 52-week high[/dim]")
        
        console.print()
        
        # Near 52-Week Low
        if near_low:
            table = Table(
                title=f"🔻 Near 52-Week LOW ({len(near_low)} stocks)",
                box=box.ROUNDED,
                header_style="bold red"
            )
            table.add_column("Symbol", style="bold white")
            table.add_column("LTP", justify="right")
            table.add_column("52W Low", justify="right", style="red")
            table.add_column("Gap", justify="right")
            
            for stock in near_low[:15]:
                ltp = stock.get('close', 0)
                low = stock.get('min_close', 0)
                gap = stock.get('above_min_percentage', 0)
                table.add_row(
                    stock.get('symbol', 'N/A'),
                    f"Rs. {ltp:,.2f}",
                    f"Rs. {low:,.2f}",
                    f"[red]+{gap:.2f}%[/red]"
                )
            console.print(table)
        else:
            console.print("[dim]No stocks currently near 52-week low[/dim]")
            
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def cmd_holidays() -> None:
    """Display market holidays."""
    try:
        with console.status("[bold green]Fetching holidays...", spinner="dots"):
            response = requests.get(
                "https://sharehubnepal.com/data/api/v1/holiday",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        
        holidays = data.get('data', []) if data.get('success') else []
        
        if not holidays:
            console.print("[yellow]No holiday data available[/yellow]")
            return
        
        # Filter upcoming holidays
        today = datetime.now()
        upcoming = []
        past = []
        
        for h in holidays:
            try:
                date_str = h.get('date', '')
                holiday_date = datetime.fromisoformat(date_str.replace('Z', ''))
                if holiday_date >= today:
                    upcoming.append((holiday_date, h))
                else:
                    past.append((holiday_date, h))
            except:
                continue
        
        upcoming.sort(key=lambda x: x[0])
        past.sort(key=lambda x: x[0], reverse=True)
        
        # Upcoming Holidays
        table = Table(
            title=f"📅 Upcoming Market Holidays ({len(upcoming)})",
            box=box.ROUNDED,
            header_style="bold cyan"
        )
        table.add_column("Date", style="bold white")
        table.add_column("Day", style="yellow")
        table.add_column("Occasion", style="cyan")
        
        for date, h in upcoming[:10]:
            table.add_row(
                date.strftime("%d %b %Y"),
                date.strftime("%A"),
                h.get('description', 'N/A')
            )
        
        console.print(table)
        
        if past:
            console.print(f"\n[dim]Past holidays this year: {len(past)}[/dim]")
            
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def cmd_floor(symbol: Optional[str] = None, date: Optional[str] = None, 
               buyer_id: Optional[str] = None, seller_id: Optional[str] = None,
               page: int = 1, size: int = 50) -> None:
    """
    Display floorsheet data with filtering options.
    
    Args:
        symbol: Stock symbol to filter (e.g., NABIL)
        date: Date in YYYY-MM-DD format (e.g., 2026-01-15). 
              If not provided, returns LIVE data (broker info will be null).
              If provided, returns HISTORICAL data with broker names.
        buyer_id: Filter by buyer broker ID (e.g., 58)
        seller_id: Filter by seller broker ID (e.g., 59)
        page: Page number (default 1)
        size: Number of records (default 50, max 100)
    """
    try:
        # Validate and parse date if provided
        if date:
            # Support multiple date formats
            import re
            from datetime import datetime
            
            date_str = date.strip()
            parsed_date = None
            
            # Try YYYY-MM-DD format first
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                try:
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    pass
            # Try DD-MM-YYYY format
            elif re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
                try:
                    parsed_date = datetime.strptime(date_str, '%d-%m-%Y')
                except ValueError:
                    pass
            # Try DD/MM/YYYY format
            elif re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                try:
                    parsed_date = datetime.strptime(date_str, '%d/%m/%Y')
                except ValueError:
                    pass
            
            if not parsed_date:
                console.print("[red]⚠️  Invalid date format![/red]")
                console.print("[dim]Use format: YYYY-MM-DD (e.g., 2026-01-15)[/dim]")
                return
            
            # Convert to API format
            date = parsed_date.strftime('%Y-%m-%d')
        
        # Build params
        params = {
            "Size": min(size, 100),  # Max 100
            "page": max(page, 1)     # Min 1
        }
        
        if symbol:
            params["symbol"] = symbol.upper()
        if date:
            params["date"] = date
        if buyer_id:
            params["BuyerId"] = buyer_id
        if seller_id:
            params["SellerId"] = seller_id
        
        # Show what we're fetching
        filter_info = []
        if symbol:
            filter_info.append(f"Symbol: {symbol.upper()}")
        if date:
            filter_info.append(f"Date: {date}")
        if buyer_id:
            filter_info.append(f"Buyer: #{buyer_id}")
        if seller_id:
            filter_info.append(f"Seller: #{seller_id}")
        
        status_msg = "[bold green]Fetching "
        status_msg += "historical" if date else "LIVE"
        status_msg += " floorsheet..."
        
        with console.status(status_msg, spinner="dots"):
            response = requests.get(
                "https://sharehubnepal.com/live/api/v2/floorsheet",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
        
        content = data.get('data', {}).get('content', [])
        
        if not content:
            msg = "No floorsheet data found"
            if filter_info:
                msg += f" for filters: {', '.join(filter_info)}"
            console.print(f"[yellow]{msg}[/yellow]")
            return
        
        total_amt = data.get('data', {}).get('totalAmount', 0)
        total_qty = data.get('data', {}).get('totalQty', 0)
        total_trades = data.get('data', {}).get('totalTrades', 0)
        total_pages = data.get('data', {}).get('totalPages', 1)
        
        # Build title
        title_parts = ["📋 Floorsheet"]
        if date:
            title_parts.append(f"[cyan]({date})[/cyan]")
        else:
            title_parts.append("[green](LIVE)[/green]")
        if symbol:
            title_parts.append(f"- {symbol.upper()}")
        
        table = Table(
            title=" ".join(title_parts),
            box=box.ROUNDED,
            header_style="bold cyan",
            caption=f"Page {page}/{total_pages}" if total_pages > 1 else None
        )
        table.add_column("Symbol", style="bold white")
        table.add_column("Buyer", justify="right", style="green")
        table.add_column("Seller", justify="right", style="red")
        table.add_column("Qty", justify="right")
        table.add_column("Rate", justify="right")
        table.add_column("Amount", justify="right", style="yellow")
        
        for item in content[:30]:
            # Always use broker IDs (buyerMemberId, sellerMemberId)
            buyer = str(item.get('buyerMemberId') or '-')
            seller = str(item.get('sellerMemberId') or '-')
            
            table.add_row(
                item.get('symbol', 'N/A'),
                buyer,
                seller,
                f"{item.get('contractQuantity', 0):,}",
                f"{item.get('contractRate', 0):,.2f}",
                format_number(item.get('contractAmount', 0))
            )
        
        console.print(table)
        
        # Summary
        summary_parts = [
            f"Total Trades: [cyan]{total_trades:,}[/cyan]",
            f"Total Qty: [cyan]{total_qty:,}[/cyan]",
            f"Total Amount: [yellow]Rs. {total_amt:,.2f}[/yellow]"
        ]
        
        console.print(Panel(
            "  |  ".join(summary_parts),
            box=box.ROUNDED,
            style="dim"
        ))
        
        # Show filter info and hints
        if filter_info:
            console.print(f"[dim]Filters: {', '.join(filter_info)}[/dim]")
        
        # Show helpful hints based on what parameters are already used
        hints = []
        if not symbol:
            hints.append("Add symbol: floor NABIL")
        if not date:
            hints.append("Add date: --date 2026-01-15")
        if not buyer_id and not seller_id:
            hints.append("Filter by broker: --buyer 58 or --seller 59")
        
        if hints:
            console.print(f"[dim]💡 Tip: {' | '.join(hints)}[/dim]")
        
        if total_pages > 1:
            console.print(f"[dim]📄 More pages available. Use --page {page+1} to see next page[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def cmd_brokers() -> None:
    """Display list of all brokers."""
    try:
        with console.status("[bold green]Fetching brokers...", spinner="dots"):
            response = requests.get(
                "https://chukul.com/api/broker/",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        
        if not data:
            console.print("[yellow]No broker data available[/yellow]")
            return
        
        # Sort by broker number
        data.sort(key=lambda x: int(x.get('broker_no', 0)))
        
        table = Table(
            title=f"🏢 NEPSE Brokers ({len(data)})",
            box=box.ROUNDED,
            header_style="bold cyan"
        )
        table.add_column("No.", style="bold yellow", width=5)
        table.add_column("Name", style="white")
        table.add_column("Short", style="dim")
        
        for broker in data:
            table.add_row(
                str(broker.get('broker_no', 'N/A')),
                broker.get('broker_name', 'N/A'),
                broker.get('code', '')
            )
        
        console.print(table)
        console.print(Panel(
            "💡 Use broker numbers when analyzing floorsheet data",
            box=box.ROUNDED,
            style="dim"
        ))
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def cmd_signals() -> None:
    """Display strong buy/sell signals."""
    try:
        with console.status("[bold green]Fetching signals...", spinner="dots"):
            buy_resp = requests.get("https://chukul.com/api/data/strong-buy/", timeout=10)
            sell_resp = requests.get("https://chukul.com/api/data/strong-sell/", timeout=10)
            
            buy_data = buy_resp.json() if buy_resp.status_code == 200 else []
            sell_data = sell_resp.json() if sell_resp.status_code == 200 else []
        
        # Strong Buy Table
        if buy_data:
            table = Table(
                title=f"💪 STRONG BUY Signals ({len(buy_data)} stocks)",
                box=box.ROUNDED,
                header_style="bold green"
            )
            table.add_column("Symbol", style="bold white")
            table.add_column("Buy Price", justify="right", style="green")
            table.add_column("Buy Qty", justify="right")
            table.add_column("Sell Price", justify="right", style="red")
            table.add_column("Sell Qty", justify="right")
            table.add_column("Rank", justify="center")
            
            for stock in buy_data[:15]:
                table.add_row(
                    stock.get('symbol', 'N/A'),
                    f"Rs. {stock.get('buy_price', 0):,.2f}",
                    format_number(stock.get('buy_quantity', 0)),
                    f"Rs. {stock.get('sell_price', 0):,.2f}",
                    format_number(stock.get('sell_quantity', 0)),
                    str(stock.get('order_rank', '-'))
                )
            console.print(table)
        else:
            console.print("[dim]No strong buy signals today[/dim]")
        
        console.print()
        
        # Strong Sell Table
        if sell_data:
            table = Table(
                title=f"⚠️ STRONG SELL Signals ({len(sell_data)} stocks)",
                box=box.ROUNDED,
                header_style="bold red"
            )
            table.add_column("Symbol", style="bold white")
            table.add_column("Buy Price", justify="right", style="green")
            table.add_column("Buy Qty", justify="right")
            table.add_column("Sell Price", justify="right", style="red")
            table.add_column("Sell Qty", justify="right")
            table.add_column("Rank", justify="center")
            
            for stock in sell_data[:15]:
                table.add_row(
                    stock.get('symbol', 'N/A'),
                    f"Rs. {stock.get('buy_price', 0):,.2f}",
                    format_number(stock.get('buy_quantity', 0)),
                    f"Rs. {stock.get('sell_price', 0):,.2f}",
                    format_number(stock.get('sell_quantity', 0)),
                    str(stock.get('order_rank', '-'))
                )
            console.print(table)
        else:
            console.print("[dim]No strong sell signals today[/dim]")
        
        console.print(Panel(
            "💡 Signals based on technical indicators and broker activity",
            box=box.ROUNDED,
            style="dim"
        ))
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def cmd_announce() -> None:
    """Display market announcements."""
    try:
        with console.status("[bold green]Fetching announcements...", spinner="dots"):
            response = requests.get(
                "https://chukul.com/api/report/",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        
        if not data:
            console.print("[yellow]No announcements available[/yellow]")
            return
        
        table = Table(
            title=f"📢 Market Announcements ({len(data[:20])} of {len(data)})",
            box=box.ROUNDED,
            header_style="bold cyan"
        )
        table.add_column("Symbol", style="bold yellow", width=10)
        table.add_column("Type", style="magenta", width=15)
        table.add_column("Details", style="white")
        table.add_column("Date", style="dim", width=12)
        
        for item in data[:20]:
            # Parse the announcement type
            report_type = item.get('report_type', 'N/A')
            symbol = item.get('symbol', 'N/A')
            
            # Format date
            date_str = item.get('date', '')
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', ''))
                date_display = date_obj.strftime("%d %b")
            except:
                date_display = date_str[:10] if date_str else 'N/A'
            
            # Get details
            details = item.get('title', '') or item.get('description', '') or 'N/A'
            if len(details) > 50:
                details = details[:47] + "..."
            
            table.add_row(symbol, report_type, details, date_display)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def cmd_profile(symbol: str) -> None:
    """Display company profile."""
    try:
        symbol = symbol.upper()
        
        with console.status(f"[bold green]Fetching profile for {symbol}...", spinner="dots"):
            response = requests.get(
                f"https://sharehubnepal.com/data/api/v1/security/seo-metadata/{symbol}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        
        if not data.get('success'):
            console.print(f"[red]⚠️  Profile not found for {symbol}[/red]")
            return
        
        security = data.get('data', {}).get('securityData', {})
        general = data.get('data', {}).get('generalInfo', {})
        dividend = data.get('data', {}).get('dividendRightShareData', {})
        
        if not security:
            console.print(f"[red]⚠️  No data available for {symbol}[/red]")
            return
        
        # Company Info Panel
        name = security.get('name', 'N/A')
        sector = security.get('sector', 'N/A')
        website = security.get('website', '')
        email = security.get('email', '')
        
        info_grid = Table.grid(expand=True, padding=(0, 2))
        info_grid.add_column(style="bold cyan")
        info_grid.add_column(style="white")
        
        info_grid.add_row("Company", name)
        info_grid.add_row("Symbol", symbol)
        info_grid.add_row("Sector", sector)
        if website:
            info_grid.add_row("Website", f"[link={website}]{website}[/link]")
        if email:
            info_grid.add_row("Email", email)
        
        console.print(Panel(info_grid, title=f"🏢 {symbol} - Company Profile", box=box.ROUNDED))
        
        # Market Cap & Share Structure
        market_cap = general.get('marketCap', 0)
        float_cap = general.get('floatCap', 0)
        listed_shares = general.get('listedShares', 0)
        public_shares = general.get('publicShares', 0)
        promoter_shares = general.get('promoterShares', 0)
        face_value = general.get('faceValue', 0)
        
        share_grid = Table.grid(expand=True, padding=(0, 2))
        share_grid.add_column(style="bold white")
        share_grid.add_column(justify="right", style="cyan")
        share_grid.add_column(style="bold white")
        share_grid.add_column(justify="right", style="cyan")
        
        share_grid.add_row(
            "Market Cap", format_number(market_cap),
            "Float Cap", format_number(float_cap)
        )
        share_grid.add_row(
            "Listed Shares", f"{listed_shares:,}",
            "Face Value", f"Rs. {face_value}"
        )
        share_grid.add_row(
            "Public Shares", f"{public_shares:,}",
            "Promoter Shares", f"{promoter_shares:,}"
        )
        
        console.print(Panel(share_grid, title="📊 Share Structure", box=box.ROUNDED))
        
        # 52-Week Range
        high_52 = general.get('fiftyTwoWeekHigh', 0)
        low_52 = general.get('fiftyTwoWeekLow', 0)
        ath = general.get('allTimeHigh', 0)
        atl = general.get('allTimeLow', 0)
        
        range_grid = Table.grid(expand=True, padding=(0, 2))
        range_grid.add_column(style="bold white")
        range_grid.add_column(justify="right")
        
        range_grid.add_row("52-Week High", f"[green]Rs. {high_52:,.2f}[/green]")
        range_grid.add_row("52-Week Low", f"[red]Rs. {low_52:,.2f}[/red]")
        range_grid.add_row("All-Time High", f"[green]Rs. {ath:,.2f}[/green]")
        range_grid.add_row("All-Time Low", f"[red]Rs. {atl:,.2f}[/red]")
        
        console.print(Panel(range_grid, title="📈 Price Range", box=box.ROUNDED))
        
        # Last Dividend
        last_div = dividend.get('lastDividend', {})
        if last_div:
            bonus = last_div.get('bonus', 0)
            cash = last_div.get('cash', 0)
            total = last_div.get('total', 0)
            fy = last_div.get('fiscalYear', 'N/A')
            
            div_text = f"FY {fy}: [yellow]{total}%[/yellow] (Bonus: {bonus}%, Cash: {cash}%)"
            console.print(Panel(div_text, title="💰 Last Dividend", box=box.ROUNDED))
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def cmd_fundamental(symbol: str) -> None:
    """Display stock fundamentals."""
    try:
        symbol = symbol.upper()
        
        with console.status(f"[bold green]Fetching fundamentals for {symbol}...", spinner="dots"):
            # Get stock list to find ID and sector
            stock_list_resp = requests.get("https://chukul.com/api/stock/", timeout=10)
            stock_list = stock_list_resp.json() if stock_list_resp.status_code == 200 else []
            
            stock_info = next((s for s in stock_list if s.get('symbol') == symbol), None)
            
            if not stock_info:
                console.print(f"[red]⚠️  Stock {symbol} not found[/red]")
                return
            
            stock_id = stock_info.get('id')
            sector_id = stock_info.get('sector', 1)
            
            # Fetch fundamentals
            details_resp = requests.get(
                "https://chukul.com/api/data/stock-details/",
                params={"symbol": symbol, "sector": sector_id},
                timeout=10
            )
            details = details_resp.json() if details_resp.status_code == 200 else {}
            
            # Fetch dividend history
            bonus_resp = requests.get(
                "https://chukul.com/api/bonus/",
                params={"symbol": symbol},
                timeout=10
            )
            bonus_data = bonus_resp.json() if bonus_resp.status_code == 200 else []
        
        if not details:
            console.print(f"[red]⚠️  No fundamental data for {symbol}[/red]")
            return
        
        # Key Metrics Panel
        eps = details.get('eps_a', 0) or details.get('eps', 0)
        pe = details.get('pe_ratio', 0)
        pb = details.get('pb_ratio', 0)
        roe = details.get('roe', 0)
        net_worth = details.get('net_worth', 0)
        gram_value = details.get('gram_value', 0)
        
        metrics_table = Table(box=box.ROUNDED, header_style="bold cyan")
        metrics_table.add_column("Metric", style="bold white")
        metrics_table.add_column("Value", justify="right", style="yellow")
        metrics_table.add_column("Metric", style="bold white")
        metrics_table.add_column("Value", justify="right", style="yellow")
        
        metrics_table.add_row("EPS", f"Rs. {eps:.2f}", "P/E Ratio", f"{pe:.2f}")
        metrics_table.add_row("P/B Ratio", f"{pb:.2f}", "ROE", f"{roe:.2f}%")
        metrics_table.add_row("Net Worth", f"Rs. {net_worth:.2f}", "Graham Value", f"Rs. {gram_value:.2f}")
        
        console.print(Panel(metrics_table, title=f"📊 {symbol} Fundamentals", box=box.ROUNDED))
        
        # Valuation Analysis
        close_price = details.get('close', 0)
        if close_price > 0 and gram_value > 0:
            discount = ((gram_value - close_price) / gram_value) * 100
            if discount > 0:
                val_text = f"[green]Trading {discount:.1f}% BELOW Graham Value (Undervalued)[/green]"
            else:
                val_text = f"[red]Trading {abs(discount):.1f}% ABOVE Graham Value (Overvalued)[/red]"
            console.print(Panel(val_text, title="💡 Valuation", box=box.ROUNDED))
        
        # Dividend History
        if bonus_data:
            div_table = Table(
                title="📅 Dividend History",
                box=box.ROUNDED,
                header_style="bold magenta"
            )
            div_table.add_column("Year", style="cyan")
            div_table.add_column("Bonus %", justify="right", style="green")
            div_table.add_column("Cash %", justify="right", style="yellow")
            div_table.add_column("Total %", justify="right", style="bold white")
            
            for div in bonus_data[:5]:
                div_table.add_row(
                    div.get('year', 'N/A'),
                    f"{div.get('bonus', 0):.2f}",
                    f"{div.get('cash', 0):.2f}",
                    f"{div.get('total', 0):.2f}"
                )
            
            console.print(div_table)
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def cmd_depth(symbol: str) -> None:
    """Display market depth (order book)."""
    try:
        symbol = symbol.upper()
        
        # First get security ID
        with console.status(f"[bold green]Fetching market depth for {symbol}...", spinner="dots"):
            live_resp = requests.get(
                "https://sharehubnepal.com/live/api/v2/nepselive/live-nepse",
                timeout=10
            )
            live_data = live_resp.json() if live_resp.status_code == 200 else {}
            
            stocks = live_data.get('data', [])
            stock_info = next((s for s in stocks if s.get('symbol') == symbol), None)
            
            if not stock_info:
                console.print(f"[red]⚠️  Stock {symbol} not found[/red]")
                return
            
            security_id = stock_info.get('securityId')
            
            if not security_id:
                console.print(f"[red]⚠️  Security ID not found for {symbol}[/red]")
                return
            
            # Get market depth
            depth_resp = requests.get(
                f"https://sharehubnepal.com/live/api/v1/nepselive/market-depth/{security_id}",
                timeout=10
            )
            depth_data = depth_resp.json() if depth_resp.status_code == 200 else {}
        
        buy_orders = depth_data.get('data', {}).get('buyMarketDepthList', [])
        sell_orders = depth_data.get('data', {}).get('sellMarketDepthList', [])
        
        if not buy_orders and not sell_orders:
            console.print(f"[yellow]No market depth data for {symbol}[/yellow]")
            console.print("[dim]💡 Market depth is only available during trading hours (11:00 AM - 3:00 PM)[/dim]")
            return
        
        # Create side-by-side table
        depth_table = Table(
            title=f"📊 Market Depth - {symbol}",
            box=box.ROUNDED,
            header_style="bold cyan"
        )
        
        # Buy side columns
        depth_table.add_column("Buy Qty", justify="right", style="green")
        depth_table.add_column("Buy Orders", justify="right", style="green")
        depth_table.add_column("Buy Price", justify="right", style="bold green")
        
        # Separator
        depth_table.add_column("", width=3)
        
        # Sell side columns
        depth_table.add_column("Sell Price", justify="right", style="bold red")
        depth_table.add_column("Sell Orders", justify="right", style="red")
        depth_table.add_column("Sell Qty", justify="right", style="red")
        
        max_rows = max(len(buy_orders), len(sell_orders), 1)
        
        for i in range(min(max_rows, 10)):
            buy = buy_orders[i] if i < len(buy_orders) else {}
            sell = sell_orders[i] if i < len(sell_orders) else {}
            
            depth_table.add_row(
                f"{buy.get('quantity', 0):,}" if buy else "",
                str(buy.get('orderCount', '')) if buy else "",
                f"{buy.get('price', 0):,.2f}" if buy else "",
                "│",
                f"{sell.get('price', 0):,.2f}" if sell else "",
                str(sell.get('orderCount', '')) if sell else "",
                f"{sell.get('quantity', 0):,}" if sell else ""
            )
        
        console.print(depth_table)
        
        # Summary
        total_buy_qty = sum(o.get('quantity', 0) for o in buy_orders)
        total_sell_qty = sum(o.get('quantity', 0) for o in sell_orders)
        
        ratio = total_buy_qty / total_sell_qty if total_sell_qty > 0 else 0
        pressure = "🟢 BUY PRESSURE" if ratio > 1.2 else "🔴 SELL PRESSURE" if ratio < 0.8 else "⚪ BALANCED"
        
        console.print(Panel(
            f"Buy Qty: [green]{total_buy_qty:,}[/green]  |  "
            f"Sell Qty: [red]{total_sell_qty:,}[/red]  |  "
            f"Ratio: [yellow]{ratio:.2f}[/yellow]  |  {pressure}",
            box=box.ROUNDED
        ))
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")


def cmd_sectors() -> None:
    """Display all sectors with IDs."""
    try:
        with console.status("[bold green]Fetching sectors...", spinner="dots"):
            response = requests.get(
                "https://chukul.com/api/sector/",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        
        if not data:
            console.print("[yellow]No sector data available[/yellow]")
            return
        
        table = Table(
            title="🏢 NEPSE Sectors",
            box=box.ROUNDED,
            header_style="bold cyan"
        )
        table.add_column("ID", style="bold yellow", width=5)
        table.add_column("Code", style="magenta", width=15)
        table.add_column("Sector Name", style="white")
        table.add_column("Stocks", justify="right", style="cyan")
        
        for sector in data:
            stocks = sector.get('stocks', [])
            table.add_row(
                str(sector.get('id', 'N/A')),
                sector.get('symbol', 'N/A'),
                sector.get('name', 'N/A'),
                str(len(stocks))
            )
        
        console.print(table)
        console.print(Panel(
            "💡 Use [bold cyan]subidx <sector>[/] to view sector index details",
            box=box.ROUNDED,
            style="dim"
        ))
        
    except Exception as e:
        console.print(f"[bold red]⚠️  Error:[/bold red] {str(e)}\n")

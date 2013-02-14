module Main where

-- import Text.ParserCombinators.Parsec

import Data.GraphViz
import qualified Data.Text.Lazy as B
import qualified Data.Text.Lazy.IO as L
import qualified Data.GraphViz.Types.Generalised as G
import qualified Data.GraphViz.Types as Par
import qualified Data.GraphViz as Gr
import Data.Text.IO as T
import System.IO as S
import qualified Data.GraphViz.Commands.IO as Pario
-- import Prelude
import qualified Data.Map.Lazy as Map
-- import IO
plop :: Int -> String

plop 1 = "bidou"
plop _ = "wow"

-- let 
path = "./cats.dot" :: String 

edges :: (Ord n) => G.DotGraph n -> [ n ]

edges graph = 
	let plop2 = graphNodes graph in
		map (\x ->  nodeID x ) $ plop2


toDotNodes :: (Ord n) => NodeLookup n -> [DotNode n]
toDotNodes = map (\(n,(_,as)) -> DotNode n as) . Map.assocs


main = do 
	dotText <- L.readFile path
	let dotGraph = parseDotGraph dotText :: G.DotGraph String
	xDotText <- graphvizWithHandle Dot dotGraph XDot T.hGetContents
	let xDotGraph =  parseDotGraph $ B.fromChunks [xDotText] :: G.DotGraph String
	S.putStrLn "plop"
	S.putStrLn "plop"
	-- graphStatements dotGraph
	S.putStrLn "plop"
	-- Pario.putDot dotGraph
	mapM S.putStrLn $ edges xDotGraph
	let inf = nodeInformation True dotGraph
	-- let nodeInf = inf Map.! "TeX" -- Map.! "TeX"
	let nodes = toDotNodes inf
	S.putStr(nodes)
	-- mapM S.putStr $ fst nodeInf


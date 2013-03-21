module Main where

-- import Text.ParserCombinators.Parsec

import Data.GraphViz
-- import Data.Graph.Inductive.Graph
import Data.Graph.Inductive

import qualified Data.Text.Lazy as B
import qualified Data.Text.Lazy.IO as L
import qualified Data.GraphViz.Types.Generalised as G
import qualified Data.GraphViz.Types as Par
import qualified Data.GraphViz as Gr
import Data.Text.IO as T
import System.IO as S
-- import qualified Data.GraphViz.Commands.IO as Pario
-- import Prelude
-- import qualified Data.Map.Lazy as Map
-- import IO
-- import qualified Data.GraphViz.Commands.IO as Pario
-- import Prelude
-- import qualified Data.Map.Lazy as Map
-- import IO

import Data.HashTable
-- import Data.Int

import Control.Arrow

plop :: Int -> String

plop 1 = "bidou"
plop _ = "wow"

-- let 
inputpath = "./output/cats.dot" :: String 

nodes_label graph = 
	let plop2 = Gr.graphNodes graph in
		map (\x ->  nodeID x ) $ plop2
nodes_label :: (Ord n) => G.DotGraph n -> [ n ]





-- toDotNodes :: (Ord n) => NodeLookup n -> [DotNode n]
-- toDotNodes = map (\(n,(_,as)) -> DotNode n as) . Map.assocs


edges_list :: (Ord n) => G.DotGraph n -> [ (n , n) ]
edges_list graph = 
	map (\edg -> (fromNode edg, toNode edg) ) $ graphEdges graph
map_couple :: (a -> b) -> (a, a) -> (b, b) 
map_couple f(a1, a2) = (f a1, f a2) 


toID :: String -> Int
toID = fromIntegral.hashString

buildGraph :: [ String ] -> [(String, String )] -> Gr String String
buildGraph noeuds aretes =
	mkGraph (map (toID &&& (\x -> x)) $ noeuds) 
		(map (toID *** toID >>> arr (\ (x,y) ->  (x,y,"") ) ) $ aretes )


main = do 
	dotText <- L.readFile inputpath
	let dotGraph = parseDotGraph dotText :: G.DotGraph String
	xDotText <- graphvizWithHandle Dot dotGraph XDot T.hGetContents
	let xDotGraph =  parseDotGraph $ B.fromChunks [xDotText] :: G.DotGraph String
	S.putStrLn "plop"
	S.putStrLn "plop"
	-- graphStatements dotGraph
	S.putStrLn "plop"
	-- Pario.putDot dotGraph
	mapM S.putStrLn $ nodes_label xDotGraph
	mapM S.putStrLn $ (nodes_label dotGraph)
	
	let noeuds = nodes_label xDotGraph
	let aretes = edges_list xDotGraph
	
	-- mapM S.putStr $ fst nodeInf
	
	-- TODO: convert to Arrows
	let gra = buildGraph noeuds aretes 
	S.putStr (show (isEmpty gra))
	S.putStrLn "Fin"


